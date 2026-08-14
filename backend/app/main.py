"""
Aurevia API — FastAPI Application Entry Point
═══════════════════════════════════════════════
Real estate intelligence platform backend.

Run in development:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Interactive docs (auto-generated):
    http://localhost:8000/docs        ← Swagger UI
    http://localhost:8000/redoc       ← ReDoc
    http://localhost:8000/openapi.json
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import create_tables
from app.models import contact as _contact_model  # noqa: F401 — registers table with Base
from app.routers import analytics, contact, properties, search, stats, waitlist


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before accepting requests, and cleanup on shutdown."""
    # Create database tables (dev only — use Alembic migrations in production)
    await create_tables()
    print("✅ Database tables ready")
    print(f"🚀 Aurevia API running | env={settings.environment}")
    yield
    print("👋 Aurevia API shutting down")


# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.project_name,
    description="""
## Aurevia — Real Estate Intelligence API

The Aurevia backend powers property search, AI match scoring, and market analytics
for the world's most intelligent real estate investment platform.

### Key Features
- 🔍 **Property Search** — Filter by location, price, bedrooms, cap rate, yield, and risk score
- 🧠 **AI Match Scoring** — Submit an investor profile and receive ranked property recommendations
- 📊 **Market Analytics** — Aggregated investment metrics per city
- 📈 **Property Analytics** — Detailed NOI, cash-on-cash, IRR, and appreciation estimates
- 📬 **Waitlist** — Early-access email capture

### Authentication
Currently open for development. JWT authentication will be added before production launch.
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(properties.router, prefix=settings.api_v1_prefix)
app.include_router(analytics.router, prefix=settings.api_v1_prefix)
app.include_router(waitlist.router, prefix=settings.api_v1_prefix)
app.include_router(stats.router, prefix=settings.api_v1_prefix)
app.include_router(search.router, prefix=settings.api_v1_prefix)
app.include_router(contact.router, prefix=settings.api_v1_prefix)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="API health check")
async def health_check():
    """Returns the current health and version of the API."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "database": "connected",
        "project": settings.project_name,
    }


@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    return JSONResponse({
        "message": "Welcome to the Aurevia API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "version": "1.0.0",
    })
