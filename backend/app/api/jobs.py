"""UMBRA — jobs.py"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter()

@router.get("")
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT * FROM analysis_runs ORDER BY created_at DESC LIMIT 50")
    )
    return [dict(r._mapping) for r in result.fetchall()]
