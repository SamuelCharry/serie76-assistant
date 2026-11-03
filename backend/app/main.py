"""Catalogue and persistent conversation API; live interpretation needs model configuration."""

import psycopg
from fastapi import FastAPI, HTTPException
from backend.conversation.api import router as conversation_router

from backend.catalog.db import connect, readiness
from backend.catalog.models import SearchFilters, validate_part_number
from backend.catalog.repository import get_actuator, search_actuators

app = FastAPI(
    title="Series 76 Assistant",
    version="0.3.0",
    description="PostgreSQL catalogue and persistent conversations. Configure OpenRouter to enable language interpretation.",
)
app.include_router(conversation_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "stage": "conversation-api"}


@app.get("/ready")
def ready():
    try:
        with connect() as connection:
            return readiness(connection)
    except (psycopg.Error, ValueError):
        raise HTTPException(
            503, detail="Database, migrations or active catalogue not ready"
        ) from None


@app.post("/api/actuators/search")
def search(filters: SearchFilters):
    try:
        with connect() as connection:
            return search_actuators(connection, filters)
    except (psycopg.Error, ValueError):
        raise HTTPException(503, detail="Catalogue unavailable") from None


@app.get("/api/actuators/{part_number:path}")
def actuator(part_number: str):
    try:
        validate_part_number(part_number)
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from None
    try:
        with connect() as connection:
            product = get_actuator(connection, part_number)
    except (psycopg.Error, ValueError):
        raise HTTPException(503, detail="Catalogue unavailable") from None
    if product is None:
        raise HTTPException(404, detail="Base Part Number not found")
    return product
