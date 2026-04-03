"""
UMBRA — Deploy Config
Free-tier optimised: Supabase + Render/Railway
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Database (Supabase connection string) ──────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@db.xxx.supabase.co:5432/postgres"

    # ── Claude / Anthropic (optional — system works without it) ──
    ANTHROPIC_API_KEY: str = ""

    # ── App ────────────────────────────────────────────────
    APP_ENV: str = "production"
    LOG_LEVEL: str = "INFO"

    # ── Demo-mode limits (keep free tier stable) ──────────
    DEMO_MODE: bool = True
    MAX_REASONING_GAPS: int = 5      # Claude calls per analysis run
    MAX_CLIENTS_PER_RUN: int = 1     # 1 client per /analyze call

    # ── CORS origins (comma-separated) ────────────────────
    CORS_ORIGINS: str = "*"          # tighten to Vercel URL in prod

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
