"""UMBRA — techniques.py"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter()

@router.get("")
async def list_techniques(
    tactic: str = Query(None),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    filters = "WHERE 1=1"
    params = {}
    if tactic:
        filters += " AND tactic = :tactic"
        params["tactic"] = tactic
    if search:
        filters += " AND (technique_id ILIKE :search OR name ILIKE :search)"
        params["search"] = f"%{search}%"

    result = await db.execute(
        text(f"SELECT * FROM mitre_techniques {filters} ORDER BY tactic, technique_id"),
        params,
    )
    return [dict(r._mapping) for r in result.fetchall()]

@router.get("/tactics")
async def list_tactics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT DISTINCT tactic, COUNT(*) as count FROM mitre_techniques GROUP BY tactic ORDER BY tactic")
    )
    return [dict(r._mapping) for r in result.fetchall()]
