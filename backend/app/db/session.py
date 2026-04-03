"""
UMBRA DB Session — Supabase / free-tier optimised
- Small pool (free Supabase = 60 connection limit)
- Pool pre-ping handles cold-start reconnects
- Connection recycling prevents stale connections on idle Render instances
"""
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger("umbra.db")

# Supabase free tier: max ~60 connections. Keep pool tiny.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=3,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "server_settings": {"application_name": "umbra-demo"},
        "command_timeout": 30,
        "statement_cache_size": 0,   # ← ADD THIS LINE
    },
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Startup DB check — retries for cold-start scenarios."""
    import asyncio
    for attempt in range(5):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✓ Database connected (Supabase)")
            return
        except Exception as e:
            logger.warning(f"DB connect attempt {attempt+1}/5 failed: {e}")
            await asyncio.sleep(2 ** attempt)
    raise RuntimeError("Could not connect to Supabase database after 5 attempts")
