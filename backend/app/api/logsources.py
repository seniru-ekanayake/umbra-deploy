"""UMBRA — logsources.py"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter()

@router.get("")
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM log_sources ORDER BY category, name"))
    return [dict(r._mapping) for r in result.fetchall()]

@router.get("/client")
async def get_client_sources(client_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("""
            SELECT ls.*, cls.active, cls.ingestion_rate_gb, cls.health
            FROM log_sources ls
            JOIN client_log_sources cls ON cls.source_id = ls.id
            WHERE cls.client_id = :client_id
        """),
        {"client_id": client_id},
    )
    return [dict(r._mapping) for r in result.fetchall()]
