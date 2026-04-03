"""UMBRA — clients.py"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter()

@router.get("")
async def list_clients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM clients WHERE active=TRUE ORDER BY name"))
    return [dict(r._mapping) for r in result.fetchall()]

@router.get("/{client_id}")
async def get_client(client_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT * FROM clients WHERE id=:id"), {"id": client_id}
    )
    row = result.fetchone()
    from fastapi import HTTPException
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return dict(row._mapping)
