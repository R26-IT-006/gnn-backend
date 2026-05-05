"""
Graph Knowledge Base service — Neo4j CRUD and edge-weight management.

Node labels:
  (:Student)   { student_id, student_key }
  (:Concept)   { concept_key, category_key, label, sequence_index }
  (:Category)  { category_key, label }

Relationship types (Tier 1):
  (:Student)-[:T1_ENGAGEMENT { tap_count, time_spent_ms, image_format, updated_at }]->(:Concept)
  (:Student)-[:T1_SCORE      { score, attempt_count, passed, updated_at }]->(:Concept)
  (:Concept)-[:CONFUSION     { weight, updated_at }]->(:Concept)
  (:Category)-[:HAS_CONCEPT]->(:Concept)
"""

from datetime import datetime, timezone
from neo4j import AsyncGraphDatabase


class GKBService:
    def __init__(self, uri: str, user: str, password: str):
        self._driver = AsyncGraphDatabase.driver(
            uri,
            auth=(user, password),
            # Check connection liveness before use — prevents SessionExpired on
            # AuraDB free-tier which drops idle connections aggressively.
            liveness_check_timeout=0,
            max_connection_lifetime=25 * 60,  # recycle before AuraDB's 30-min idle limit
            max_connection_pool_size=5,
        )

    async def close(self):
        await self._driver.close()

    async def verify_connectivity(self):
        await self._driver.verify_connectivity()

    # ─── Node helpers ────────────────────────────────────────────────────────────

    async def ensure_student_node(self, student_id: int, student_key: str, full_name: str = None) -> dict:
        async with self._driver.session() as session:
            result = await session.run(
                """
                MERGE (s:Student { student_id: $sid })
                ON CREATE SET s.student_key = $key, s.full_name = $name, s.created_at = $now
                ON MATCH SET  s.full_name = CASE WHEN $name IS NOT NULL THEN $name ELSE s.full_name END
                RETURN s
                """,
                sid=student_id,
                key=student_key,
                name=full_name,
                now=_now(),
            )
            record = await result.single()
            return dict(record["s"])

    async def ensure_concept_node(
        self,
        category_key: str,
        concept_key: str,
        label: str,
        sequence_index: int,
    ) -> dict:
        async with self._driver.session() as session:
            result = await session.run(
                """
                MERGE (c:Concept { concept_key: $ckey })
                ON CREATE SET
                    c.category_key    = $catkey,
                    c.label           = $label,
                    c.sequence_index  = $idx,
                    c.created_at      = $now
                MERGE (cat:Category { category_key: $catkey })
                MERGE (cat)-[:HAS_CONCEPT]->(c)
                RETURN c
                """,
                ckey=f"{category_key}/{concept_key}",
                catkey=category_key,
                label=label,
                idx=sequence_index,
                now=_now(),
            )
            record = await result.single()
            return dict(record["c"])

    async def seed_concepts(self, concept_list: list[dict]):
        """
        Idempotent seed.  concept_list items:
          { category_key, concept_key, label, sequence_index }
        """
        for item in concept_list:
            await self.ensure_concept_node(
                item["category_key"],
                item["concept_key"],
                item["label"],
                item["sequence_index"],
            )

    # ─── Tier 1 edge helpers ─────────────────────────────────────────────────────

    async def upsert_t1_engagement(
        self,
        student_id: int,
        concept_key: str,
        category_key: str,
        tap_count: int,
        time_spent_ms: int,
        image_format: str = "real",
        full_name: str = None,
    ) -> dict:
        full_concept_key = f"{category_key}/{concept_key}"
        async with self._driver.session() as session:
            result = await session.run(
                """
                MERGE (s:Student { student_id: $sid })
                ON CREATE SET s.student_key = $skey, s.full_name = $sname, s.created_at = $now
                ON MATCH SET  s.full_name = CASE WHEN $sname IS NOT NULL THEN $sname ELSE s.full_name END
                WITH s
                MATCH (c:Concept { concept_key: $ckey })
                MERGE (s)-[r:T1_ENGAGEMENT]->(c)
                ON CREATE SET
                    r.tap_count     = $tap,
                    r.time_spent_ms = $time,
                    r.image_format  = $fmt,
                    r.created_at    = $now,
                    r.updated_at    = $now
                ON MATCH SET
                    r.tap_count     = $tap,
                    r.time_spent_ms = $time,
                    r.image_format  = $fmt,
                    r.updated_at    = $now
                RETURN r
                """,
                sid=student_id,
                skey=f"student/{student_id}",
                sname=full_name,
                ckey=full_concept_key,
                tap=tap_count,
                time=time_spent_ms,
                fmt=image_format,
                now=_now(),
            )
            record = await result.single()
            return dict(record["r"]) if record else {}

    async def upsert_t1_score(
        self,
        student_id: int,
        concept_key: str,
        category_key: str,
        score: float,
        attempt_count: int,
        passed: bool,
        confused_with: list[dict],
        full_name: str = None,
    ) -> dict:
        """
        confused_with: [{ "selected_key": "banana", "correct_key": "apple" }, ...]
        Each wrong pair increments the CONFUSION edge weight between the two concepts.
        """
        full_concept_key = f"{category_key}/{concept_key}"
        async with self._driver.session() as session:
            result = await session.run(
                """
                MERGE (s:Student { student_id: $sid })
                ON CREATE SET s.student_key = $skey, s.full_name = $sname, s.created_at = $now
                ON MATCH SET  s.full_name = CASE WHEN $sname IS NOT NULL THEN $sname ELSE s.full_name END
                WITH s
                MATCH (c:Concept { concept_key: $ckey })
                MERGE (s)-[r:T1_SCORE]->(c)
                ON CREATE SET
                    r.score         = $score,
                    r.attempt_count = $attempts,
                    r.passed        = $passed,
                    r.created_at    = $now,
                    r.updated_at    = $now
                ON MATCH SET
                    r.score         = $score,
                    r.attempt_count = $attempts,
                    r.passed        = $passed,
                    r.updated_at    = $now
                RETURN r
                """,
                sid=student_id,
                skey=f"student/{student_id}",
                sname=full_name,
                ckey=full_concept_key,
                score=score,
                attempts=attempt_count,
                passed=passed,
                now=_now(),
            )
            record = await result.single()
            edge = dict(record["r"]) if record else {}

        # Update confusion edges
        for confusion in confused_with:
            selected_key = f"{category_key}/{confusion['selected_key']}"
            correct_key = f"{category_key}/{confusion['correct_key']}"
            await self._increment_confusion_edge(correct_key, selected_key)

        return edge

    async def _increment_confusion_edge(
        self, correct_key: str, confused_with_key: str
    ):
        """Increment weight on CONFUSION edge: correct_concept→confused_with_concept."""
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (a:Concept { concept_key: $akey })
                MATCH (b:Concept { concept_key: $bkey })
                MERGE (a)-[r:CONFUSION]->(b)
                ON CREATE SET r.weight = 1, r.updated_at = $now
                ON MATCH  SET r.weight = r.weight + 1, r.updated_at = $now
                """,
                akey=correct_key,
                bkey=confused_with_key,
                now=_now(),
            )

    async def get_student_concept_edges(
        self, student_id: int, concept_key: str, category_key: str
    ) -> dict:
        full_concept_key = f"{category_key}/{concept_key}"
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (s:Student { student_id: $sid })
                MATCH (c:Concept { concept_key: $ckey })
                OPTIONAL MATCH (s)-[eng:T1_ENGAGEMENT]->(c)
                OPTIONAL MATCH (s)-[sc:T1_SCORE]->(c)
                RETURN
                    properties(eng) AS engagement,
                    properties(sc)  AS score
                """,
                sid=student_id,
                ckey=full_concept_key,
            )
            record = await result.single()
            if not record:
                return {"engagement": None, "score": None}
            return {
                "engagement": dict(record["engagement"]) if record["engagement"] else None,
                "score": dict(record["score"]) if record["score"] else None,
            }

    async def get_concept_confusions(self, concept_key: str, category_key: str) -> list:
        full_concept_key = f"{category_key}/{concept_key}"
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (a:Concept { concept_key: $ckey })-[r:CONFUSION]->(b:Concept)
                RETURN b.concept_key AS confused_with, r.weight AS weight
                ORDER BY r.weight DESC
                """,
                ckey=full_concept_key,
            )
            records = await result.data()
            return records

    async def get_student_confusions(
        self, student_id: int, concept_key: str, category_key: str
    ) -> list[str]:
        """
        Returns concept keys (bare, without category prefix) that this student
        confused with concept_key, ordered by CONFUSION edge weight descending.
        Uses the concept-level CONFUSION edges filtered to concepts that share
        a T1_SCORE edge from this student (i.e. concepts the student has been
        tested on in the same category session).
        """
        full_concept_key = f"{category_key}/{concept_key}"
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (s:Student { student_id: $sid })-[:T1_SCORE]->(correct:Concept { concept_key: $ckey })
                MATCH (correct)-[r:CONFUSION]->(confused:Concept)
                RETURN confused.concept_key AS full_key, r.weight AS weight
                ORDER BY r.weight DESC
                LIMIT 2
                """,
                sid=student_id,
                ckey=full_concept_key,
            )
            records = await result.data()
            # Strip category prefix: "fruits/banana" → "banana"
            return [rec["full_key"].split("/")[-1] for rec in records]

    async def get_student_category_confusions(
        self, student_id: int, category_key: str
    ) -> list[dict]:
        """
        Returns all CONFUSION edges for this student across an entire category.
        Each record: { correct_key, confused_key, weight }
        Ordered by weight descending.
        """
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (s:Student { student_id: $sid })-[:T1_SCORE]->(correct:Concept)
                WHERE correct.category_key = $catkey
                MATCH (correct)-[r:CONFUSION]->(confused:Concept)
                WHERE confused.category_key = $catkey
                RETURN
                    correct.concept_key  AS correct_key,
                    confused.concept_key AS confused_key,
                    r.weight             AS weight
                ORDER BY r.weight DESC
                """,
                sid=student_id,
                catkey=category_key,
            )
            return await result.data()

    async def record_adaptive_confusions(
        self, correct_key: str, category_key: str, confused_with: list[str]
    ):
        """Increment CONFUSION edges for adaptive quiz wrong answers."""
        for confused_key in confused_with:
            full_correct  = f"{category_key}/{correct_key}"
            full_confused = f"{category_key}/{confused_key}"
            await self._increment_confusion_edge(full_correct, full_confused)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
