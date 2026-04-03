"""UMBRA — recommendations.py"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter()

@router.get("")
async def get_recommendations(
    client_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT r.*, ls.source_key, ls.name AS source_name, ls.category,
                   ls.cost_per_gb, ls.avg_daily_gb, ls.setup_complexity
            FROM recommendations r
            LEFT JOIN log_sources ls ON ls.id = r.source_id
            WHERE r.client_id = :client_id
            ORDER BY r.priority_rank NULLS LAST, r.roi_score DESC
        """),
        {"client_id": client_id},
    )
    return [dict(r._mapping) for r in result.fetchall()]
