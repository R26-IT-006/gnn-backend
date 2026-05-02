from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/gkb", tags=["GKB"])

# Static fruit sequence — mirrors backend conceptService.js FRUIT_SEQUENCE
_DEFAULT_CONCEPTS = [
    {"category_key": "fruits", "concept_key": "apple",      "label": "Apple",        "sequence_index": 0},
    {"category_key": "fruits", "concept_key": "banana",     "label": "Banana",       "sequence_index": 1},
    {"category_key": "fruits", "concept_key": "cherry",     "label": "Cherry",       "sequence_index": 2},
    {"category_key": "fruits", "concept_key": "grapes",     "label": "Grapes",       "sequence_index": 3},
    {"category_key": "fruits", "concept_key": "guava",      "label": "Guava",        "sequence_index": 4},
    {"category_key": "fruits", "concept_key": "mango",      "label": "Mango",        "sequence_index": 5},
    {"category_key": "fruits", "concept_key": "orange",     "label": "Orange",       "sequence_index": 6},
    {"category_key": "fruits", "concept_key": "papaya",     "label": "Papaya",       "sequence_index": 7},
    {"category_key": "fruits", "concept_key": "passion",    "label": "Passion Fruit","sequence_index": 8},
    {"category_key": "fruits", "concept_key": "pineapple",  "label": "Pineapple",    "sequence_index": 9},
    {"category_key": "fruits", "concept_key": "watermelon", "label": "Watermelon",   "sequence_index": 10},
]


# ─── Request schemas ─────────────────────────────────────────────────────────

class EnsureStudentRequest(BaseModel):
    student_key: str
    full_name: Optional[str] = None


class SeedConceptItem(BaseModel):
    category_key: str
    concept_key: str
    label: str
    sequence_index: int


class SeedConceptsRequest(BaseModel):
    concepts: list[SeedConceptItem]


class Tier1EngagementRequest(BaseModel):
    student_id: int
    concept_key: str
    category_key: str
    tap_count: int
    time_spent_ms: int
    image_format: str = "real"
    full_name: Optional[str] = None


class ConfusionItem(BaseModel):
    selected_key: str
    correct_key: str


class Tier1ScoreRequest(BaseModel):
    student_id: int
    concept_key: str
    category_key: str
    score: float
    attempt_count: int
    passed: bool
    confused_with: list[ConfusionItem] = []
    full_name: Optional[str] = None


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "service": "gnn-service"}


@router.post("/seed-concepts")
async def seed_concepts(request: Request, body: Optional[SeedConceptsRequest] = None):
    gkb = request.app.state.gkb
    concepts = [c.model_dump() for c in body.concepts] if body else _DEFAULT_CONCEPTS
    await gkb.seed_concepts(concepts)
    return {"seeded": len(concepts)}


@router.post("/student/{student_id}")
async def ensure_student(student_id: int, body: EnsureStudentRequest, request: Request):
    gkb = request.app.state.gkb
    node = await gkb.ensure_student_node(student_id, body.student_key, body.full_name)
    return {"node": node}


@router.post("/tier1/engagement")
async def upsert_tier1_engagement(body: Tier1EngagementRequest, request: Request):
    gkb = request.app.state.gkb
    edge = await gkb.upsert_t1_engagement(
        student_id=body.student_id,
        concept_key=body.concept_key,
        category_key=body.category_key,
        tap_count=body.tap_count,
        time_spent_ms=body.time_spent_ms,
        image_format=body.image_format,
        full_name=body.full_name,
    )
    return {"edge": edge}


@router.post("/tier1/score")
async def upsert_tier1_score(body: Tier1ScoreRequest, request: Request):
    gkb = request.app.state.gkb
    edge = await gkb.upsert_t1_score(
        student_id=body.student_id,
        concept_key=body.concept_key,
        category_key=body.category_key,
        score=body.score,
        attempt_count=body.attempt_count,
        passed=body.passed,
        confused_with=[c.model_dump() for c in body.confused_with],
        full_name=body.full_name,
    )
    return {"edge": edge}


@router.get("/student/{student_id}/concept/{category_key}/{concept_key}")
async def get_student_concept_edges(
    student_id: int,
    category_key: str,
    concept_key: str,
    request: Request,
):
    gkb = request.app.state.gkb
    data = await gkb.get_student_concept_edges(student_id, concept_key, category_key)
    return data


@router.get("/concept/{category_key}/{concept_key}/confusions")
async def get_concept_confusions(
    category_key: str,
    concept_key: str,
    request: Request,
):
    gkb = request.app.state.gkb
    data = await gkb.get_concept_confusions(concept_key, category_key)
    return {"confusions": data}
