"""UMBRA — gaps.py"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter()

@router.get("")
async def get_gaps(
    client_id: str = Query(...),
    gap_type: str = Query(None),
    severity: str = Query(None),
    resolved: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    filters = "WHERE g.client_id = :client_id AND g.resolved = :resolved"
    params = {"client_id": client_id, "resolved": resolved}
    if gap_type:
        filters += " AND g.gap_type = :gap_type"
        params["gap_type"] = gap_type
    if severity:
        filters += " AND g.severity = :severity"
        params["severity"] = severity

    result = await db.execute(
        text(f"""
            SELECT g.*, mt.name AS technique_name, mt.tactic
            FROM gaps g
            JOIN mitre_techniques mt ON mt.technique_id = g.technique_id
            {filters}
            ORDER BY g.priority_score DESC
        """),
        params,
    )
    return [dict(r._mapping) for r in result.fetchall()]

@router.get("/{gap_id}/reasoning")
async def get_gap_reasoning(
    gap_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT g.*, mt.name AS technique_name, mt.tactic, mt.description
            FROM gaps g
            JOIN mitre_techniques mt ON mt.technique_id = g.technique_id
            WHERE g.id = :gap_id
        """),
        {"gap_id": gap_id},
    )
    row = result.fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Gap not found")
    return dict(row._mapping)
