"""UMBRA analyze.py — includes /trigger-all for cron/demo preload"""
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.analysis import run_client_analysis
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger("umbra.api.analyze")


class AnalyzeRequest(BaseModel):
    client_id: str
    run_type: str = "full"


@router.post("/analyze")
async def trigger_analysis(req: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """Run full analysis for one client."""
    logger.info(f"Analysis requested for {req.client_id}")
    try:
        result = await run_client_analysis(db, req.client_id)
        return {"status": "completed", "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/all-demo")
async def trigger_all_demo_clients(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger analysis for ALL demo clients sequentially.
    Called by: cron job, Render cron, or manual demo prep.
    Replaces the background scheduler for free-tier deployment.
    """
    result = await db.execute(text("SELECT id, name FROM clients WHERE active=TRUE"))
    clients = [dict(r._mapping) for r in result.fetchall()]

    results = []
    for client in clients:
        try:
            async with __import__("app.db.session", fromlist=["AsyncSessionLocal"]).AsyncSessionLocal() as session:
                r = await run_client_analysis(session, str(client["id"]))
                results.append({"client": client["name"], "status": "ok",
                                 "gaps": r["gaps_count"], "recs": r["recommendations_count"]})
        except Exception as e:
            logger.error(f"Failed for {client['name']}: {e}")
            results.append({"client": client["name"], "status": "error", "error": str(e)})

    return {"status": "completed", "clients": results}
