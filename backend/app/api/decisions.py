"""UMBRA — decisions.py (HITL)"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db

router = APIRouter()


class DecisionRequest(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    description: Optional[str] = None
    priority: int = 50
    client_id: str


class DecisionUpdate(BaseModel):
    action: str  # approved, rejected, deferred, escalated
    decided_by: str
    rationale: Optional[str] = None


@router.get("")
async def get_decisions(
    client_id: str = Query(None),
    pending_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    filters = "WHERE 1=1"
    params = {}
    if client_id:
        filters += " AND client_id = :client_id"
        params["client_id"] = client_id
    if pending_only:
        filters += " AND action IS NULL"

    result = await db.execute(
        text(f"SELECT * FROM decisions {filters} ORDER BY priority ASC, created_at ASC"),
        params,
    )
    return [dict(r._mapping) for r in result.fetchall()]


@router.post("")
async def create_decision(req: DecisionRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("""
            INSERT INTO decisions (client_id, entity_type, entity_id, title, description, priority)
            VALUES (:client_id, :entity_type, :entity_id, :title, :description, :priority)
            RETURNING id
        """),
        req.model_dump(),
    )
    await db.commit()
    return {"id": str(result.scalar())}


@router.post("/{decision_id}")
async def submit_decision(
    decision_id: str,
    update: DecisionUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            UPDATE decisions
            SET action = :action, decided_by = :decided_by,
                rationale = :rationale, decided_at = NOW()
            WHERE id = :decision_id
            RETURNING id
        """),
        {"decision_id": decision_id, **update.model_dump()},
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Decision not found")

    # Audit log
    await db.execute(
        text("""
            INSERT INTO audit_log (actor, action, entity_type, entity_id)
            VALUES (:actor, :action, 'decision', :entity_id)
        """),
        {"actor": update.decided_by, "action": update.action, "entity_id": decision_id},
    )
    await db.commit()
    return {"status": "recorded"}
