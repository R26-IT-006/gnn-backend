import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.gkb_service import GKBService
from routers import gkb as gkb_router

load_dotenv()

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: open Neo4j driver and verify connection
    gkb = GKBService(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    await gkb.verify_connectivity()
    app.state.gkb = gkb
    print(f"[GNN Service] Connected to Neo4j at {NEO4J_URI}")
    yield
    # Shutdown: close the driver
    await gkb.close()
    print("[GNN Service] Neo4j driver closed")


app = FastAPI(
    title="Auriva GNN Service",
    description="Graph Knowledge Base and GNN inference service for Auriva adaptive learning",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gkb_router.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "auriva-gnn"}
