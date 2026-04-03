"""
UMBRA — FastAPI Entry Point
Free-tier production build (Render / Railway)
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import init_db
from app.api import (
    analyze, techniques, coverage, gaps,
    recommendations, decisions, clients, logsources, jobs,
)

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("umbra")


# ── Lifespan ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"UMBRA starting — env={settings.APP_ENV}, demo={settings.DEMO_MODE}")
    await init_db()
    logger.info("UMBRA ready.")
    yield
    logger.info("UMBRA shutting down.")


# ── App ───────────────────────────────────────────────────
app = FastAPI(
    title="UMBRA — Detection Coverage Intelligence",
    description="MITRE ATT&CK-driven MDR detection gap analysis platform",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)

# CORS — allow Vercel + localhost for dev
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ─────────────────────────────
@app.middleware("http")
async def add_timing(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
        ms = round((time.time() - start) * 1000)
        response.headers["X-Response-Time"] = f"{ms}ms"
        if ms > 3000:
            logger.warning(f"Slow request: {request.method} {request.url.path} ({ms}ms)")
        return response
    except Exception as exc:
        logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "path": str(request.url.path)},
        )


# ── Routers ───────────────────────────────────────────────
app.include_router(clients.router,         prefix="/api/clients",         tags=["Clients"])
app.include_router(analyze.router,         prefix="/api",                 tags=["Analysis"])
app.include_router(techniques.router,      prefix="/api/techniques",      tags=["Techniques"])
app.include_router(coverage.router,        prefix="/api/coverage",        tags=["Coverage"])
app.include_router(gaps.router,            prefix="/api/gaps",            tags=["Gaps"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(decisions.router,       prefix="/api/decisions",       tags=["Decisions"])
app.include_router(logsources.router,      prefix="/api/logsources",      tags=["Log Sources"])
app.include_router(jobs.router,            prefix="/api/jobs",            tags=["Jobs"])


# ── Health endpoints ──────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    """
    Used by Render/Railway to check if the service is alive.
    Also called by frontend on load to detect cold starts.
    """
    return {
        "status": "ok",
        "service": "umbra",
        "env": settings.APP_ENV,
        "demo_mode": settings.DEMO_MODE,
        "claude_enabled": bool(settings.ANTHROPIC_API_KEY),
    }


@app.get("/health/db", tags=["System"])
async def health_db():
    """Deep health check — verifies DB connectivity."""
    from app.db.session import engine
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT COUNT(*) as clients FROM clients"
            ))
            row = result.fetchone()
            return {"status": "ok", "clients_loaded": row[0] if row else 0}
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": str(e)},
        )


@app.get("/", tags=["System"])
async def root():
    return {
        "service": "UMBRA Detection Coverage Intelligence",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
