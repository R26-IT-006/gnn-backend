from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/gkb", tags=["GKB"])

# Static fruit sequence — mirrors backend conceptService.js FRUIT_SEQUENCE
_DEFAULT_CONCEPTS = [
    # Fruits
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
    # Professionals
    {"category_key": "professionals", "concept_key": "baker",     "label": "Baker",     "sequence_index": 0},
    {"category_key": "professionals", "concept_key": "carpenter", "label": "Carpenter", "sequence_index": 1},
    {"category_key": "professionals", "concept_key": "cashier",   "label": "Cashier",   "sequence_index": 2},
    {"category_key": "professionals", "concept_key": "doctor",    "label": "Doctor",    "sequence_index": 3},
    {"category_key": "professionals", "concept_key": "farmer",    "label": "Farmer",    "sequence_index": 4},
    {"category_key": "professionals", "concept_key": "nurse",     "label": "Nurse",     "sequence_index": 5},
    {"category_key": "professionals", "concept_key": "principal", "label": "Principal", "sequence_index": 6},
    {"category_key": "professionals", "concept_key": "teacher",   "label": "Teacher",   "sequence_index": 7},
    # Animals
    {"category_key": "animals", "concept_key": "ant",         "label": "Ant",         "sequence_index": 0},
    {"category_key": "animals", "concept_key": "bull",        "label": "Bull",        "sequence_index": 1},
    {"category_key": "animals", "concept_key": "butterfly",   "label": "Butterfly",   "sequence_index": 2},
    {"category_key": "animals", "concept_key": "cat",         "label": "Cat",         "sequence_index": 3},
    {"category_key": "animals", "concept_key": "caterpillar", "label": "Caterpillar", "sequence_index": 4},
    {"category_key": "animals", "concept_key": "cock",        "label": "Cock",        "sequence_index": 5},
    {"category_key": "animals", "concept_key": "cow",         "label": "Cow",         "sequence_index": 6},
    {"category_key": "animals", "concept_key": "crow",        "label": "Crow",        "sequence_index": 7},
    {"category_key": "animals", "concept_key": "dog",         "label": "Dog",         "sequence_index": 8},
    {"category_key": "animals", "concept_key": "elephant",    "label": "Elephant",    "sequence_index": 9},
    {"category_key": "animals", "concept_key": "goat",        "label": "Goat",        "sequence_index": 10},
    {"category_key": "animals", "concept_key": "hen",         "label": "Hen",         "sequence_index": 11},
    {"category_key": "animals", "concept_key": "horse",       "label": "Horse",       "sequence_index": 12},
    {"category_key": "animals", "concept_key": "lion",        "label": "Lion",        "sequence_index": 13},
    {"category_key": "animals", "concept_key": "owl",         "label": "Owl",         "sequence_index": 14},
    {"category_key": "animals", "concept_key": "parrot",      "label": "Parrot",      "sequence_index": 15},
    {"category_key": "animals", "concept_key": "peacock",     "label": "Peacock",     "sequence_index": 16},
    {"category_key": "animals", "concept_key": "rabbit",      "label": "Rabbit",      "sequence_index": 17},
    {"category_key": "animals", "concept_key": "snake",       "label": "Snake",       "sequence_index": 18},
    {"category_key": "animals", "concept_key": "sparrow",     "label": "Sparrow",     "sequence_index": 19},
    {"category_key": "animals", "concept_key": "tiger",       "label": "Tiger",       "sequence_index": 20},
    # House Parts
    {"category_key": "house", "concept_key": "door",    "label": "Door",    "sequence_index": 0},
    {"category_key": "house", "concept_key": "roof",    "label": "Roof",    "sequence_index": 1},
    {"category_key": "house", "concept_key": "wall",    "label": "Wall",    "sequence_index": 2},
    {"category_key": "house", "concept_key": "windows", "label": "Windows", "sequence_index": 3},
    # Numbers
    {"category_key": "numbers", "concept_key": "one",   "label": "One",   "sequence_index": 0},
    {"category_key": "numbers", "concept_key": "two",   "label": "Two",   "sequence_index": 1},
    {"category_key": "numbers", "concept_key": "three", "label": "Three", "sequence_index": 2},
    {"category_key": "numbers", "concept_key": "four",  "label": "Four",  "sequence_index": 3},
    {"category_key": "numbers", "concept_key": "five",  "label": "Five",  "sequence_index": 4},
    {"category_key": "numbers", "concept_key": "six",   "label": "Six",   "sequence_index": 5},
    {"category_key": "numbers", "concept_key": "seven", "label": "Seven", "sequence_index": 6},
    {"category_key": "numbers", "concept_key": "eight", "label": "Eight", "sequence_index": 7},
    {"category_key": "numbers", "concept_key": "nine",  "label": "Nine",  "sequence_index": 8},
    {"category_key": "numbers", "concept_key": "ten",   "label": "Ten",   "sequence_index": 9},
    # Shapes
    {"category_key": "shapes", "concept_key": "circle",    "label": "Circle",    "sequence_index": 0},
    {"category_key": "shapes", "concept_key": "square",    "label": "Square",    "sequence_index": 1},
    {"category_key": "shapes", "concept_key": "rectangle", "label": "Rectangle", "sequence_index": 2},
    {"category_key": "shapes", "concept_key": "triangle",  "label": "Triangle",  "sequence_index": 3},
    # Colors
    {"category_key": "colors", "concept_key": "red",    "label": "Red",    "sequence_index": 0},
    {"category_key": "colors", "concept_key": "blue",   "label": "Blue",   "sequence_index": 1},
    {"category_key": "colors", "concept_key": "green",  "label": "Green",  "sequence_index": 2},
    {"category_key": "colors", "concept_key": "yellow", "label": "Yellow", "sequence_index": 3},
    {"category_key": "colors", "concept_key": "orange", "label": "Orange", "sequence_index": 4},
    {"category_key": "colors", "concept_key": "pink",   "label": "Pink",   "sequence_index": 5},
    {"category_key": "colors", "concept_key": "purple", "label": "Purple", "sequence_index": 6},
    {"category_key": "colors", "concept_key": "brown",  "label": "Brown",  "sequence_index": 7},
    {"category_key": "colors", "concept_key": "black",  "label": "Black",  "sequence_index": 8},
    {"category_key": "colors", "concept_key": "white",  "label": "White",  "sequence_index": 9},
    # Household Items
    {"category_key": "household", "concept_key": "bed",         "label": "Bed",         "sequence_index": 0},
    {"category_key": "household", "concept_key": "brush",       "label": "Brush",       "sequence_index": 1},
    {"category_key": "household", "concept_key": "comb",        "label": "Comb",        "sequence_index": 2},
    {"category_key": "household", "concept_key": "cup",         "label": "Cup",         "sequence_index": 3},
    {"category_key": "household", "concept_key": "fork",        "label": "Fork",        "sequence_index": 4},
    {"category_key": "household", "concept_key": "glass",       "label": "Glass",       "sequence_index": 5},
    {"category_key": "household", "concept_key": "knife",       "label": "Knife",       "sequence_index": 6},
    {"category_key": "household", "concept_key": "mug",         "label": "Mug",         "sequence_index": 7},
    {"category_key": "household", "concept_key": "pillows",     "label": "Pillows",     "sequence_index": 8},
    {"category_key": "household", "concept_key": "plate",       "label": "Plate",       "sequence_index": 9},
    {"category_key": "household", "concept_key": "soap",        "label": "Soap",        "sequence_index": 10},
    {"category_key": "household", "concept_key": "spoon",       "label": "Spoon",       "sequence_index": 11},
    {"category_key": "household", "concept_key": "toothbrush",  "label": "Toothbrush",  "sequence_index": 12},
    {"category_key": "household", "concept_key": "toothpaste",  "label": "Toothpaste",  "sequence_index": 13},
    # Classroom Objects
    {"category_key": "classroom", "concept_key": "bag",        "label": "Bag",        "sequence_index": 0},
    {"category_key": "classroom", "concept_key": "blackboard", "label": "Blackboard", "sequence_index": 1},
    {"category_key": "classroom", "concept_key": "book",       "label": "Book",       "sequence_index": 2},
    {"category_key": "classroom", "concept_key": "bottle",     "label": "Bottle",     "sequence_index": 3},
    {"category_key": "classroom", "concept_key": "chair",      "label": "Chair",      "sequence_index": 4},
    {"category_key": "classroom", "concept_key": "desk",       "label": "Desk",       "sequence_index": 5},
    {"category_key": "classroom", "concept_key": "dustbin",    "label": "Dustbin",    "sequence_index": 6},
    {"category_key": "classroom", "concept_key": "eraser",     "label": "Eraser",     "sequence_index": 7},
    {"category_key": "classroom", "concept_key": "pencil",     "label": "Pencil",     "sequence_index": 8},
    {"category_key": "classroom", "concept_key": "ruler",      "label": "Ruler",      "sequence_index": 9},
    {"category_key": "classroom", "concept_key": "table",      "label": "Table",      "sequence_index": 10},
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


@router.get("/student/{student_id}/distractors")
async def get_distractors(
    student_id: int,
    request: Request,
    category_key: str = "",
    concept_key: str = "",
    tier: int = 1,
):
    """
    Returns up to 2 personalised distractor concept keys for a student + concept.
    Tier 1 → queries CONFUSION edges; Tier 2 → queries T2_NAME_CONFUSION edges.
    Returns empty list if no confusion data exists yet (caller falls back to sequential).
    """
    gkb = request.app.state.gkb
    if tier == 2:
        keys = await gkb.get_student_t2_confusions(student_id, concept_key, category_key)
    else:
        keys = await gkb.get_student_confusions(student_id, concept_key, category_key)
    return {"distractors": keys}


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


@router.get("/student/{student_id}/concept/{category_key}/{concept_key}/confusions")
async def get_student_concept_confusions(
    student_id: int,
    category_key: str,
    concept_key: str,
    request: Request,
):
    """Concept keys this student specifically confused with concept_key, sorted by weight."""
    gkb = request.app.state.gkb
    confused_keys = await gkb.get_student_confusions(student_id, concept_key, category_key)
    return {"confused_keys": confused_keys}


@router.get("/student/{student_id}/category/{category_key}/confusions")
async def get_student_category_confusions(
    student_id: int,
    category_key: str,
    request: Request,
):
    """All CONFUSION edges for a student across a whole category (for adaptive ordering)."""
    gkb = request.app.state.gkb
    confusions = await gkb.get_student_category_confusions(student_id, category_key)
    return {"confusions": confusions}


class AdaptiveConfusionRequest(BaseModel):
    correct_key: str
    category_key: str
    confused_with: list[str] = []


@router.post("/adaptive/confusion")
async def record_adaptive_confusion(body: AdaptiveConfusionRequest, request: Request):
    """Increment CONFUSION edges for wrong adaptive quiz rounds."""
    gkb = request.app.state.gkb
    await gkb.record_adaptive_confusions(body.correct_key, body.category_key, body.confused_with)
    return {"recorded": len(body.confused_with)}


class Tier2EngagementRequest(BaseModel):
    student_id: int
    concept_key: str
    category_key: str
    tap_count: int
    time_spent_ms: int
    full_name: Optional[str] = None


class Tier2ScoreRequest(BaseModel):
    student_id: int
    concept_key: str
    category_key: str
    score: float
    attempt_count: int
    passed: bool
    confused_with: list[ConfusionItem] = []
    full_name: Optional[str] = None


@router.post("/tier2/engagement")
async def upsert_tier2_engagement(body: Tier2EngagementRequest, request: Request):
    gkb = request.app.state.gkb
    edge = await gkb.upsert_t2_engagement(
        student_id=body.student_id,
        concept_key=body.concept_key,
        category_key=body.category_key,
        tap_count=body.tap_count,
        time_spent_ms=body.time_spent_ms,
        full_name=body.full_name,
    )
    return {"edge": edge}


@router.post("/tier2/score")
async def upsert_tier2_score(body: Tier2ScoreRequest, request: Request):
    gkb = request.app.state.gkb
    edge = await gkb.upsert_t2_score(
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
