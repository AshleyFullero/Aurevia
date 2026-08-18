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

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import create_tables
import app.models  # noqa: F401 — registers ALL models with Base via __init__.py
from app.routers import (
    admin,
    analytics,
    compare,
    contact,
    favorites,
    market,
    neighborhoods,
    portfolio,
    properties,
    reviews,
    search,
    stats,
    waitlist,
)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before accepting requests, and cleanup on shutdown."""
    # Create database tables (dev only — use Alembic migrations in production)
    await create_tables()
    print("[OK] Database tables ready")
    print(f"[>>] Aurevia API running | env={settings.environment}")
    yield
    print("[..] Aurevia API shutting down")


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
- 🔥 **Trending** — Hottest properties and top markets by momentum score
- ❤️  **Favorites** — Session-based property bookmarking
- ⚖️  **Compare** — Side-by-side comparison of 2–4 properties with metric winners
- 🛠️  **Admin** — Internal dashboard for properties, waitlist, and contacts
- 📬 **Waitlist** — Early-access email capture
- ⭐ **Reviews** — Investor testimonials and aggregate rating statistics
- 🏘️  **Neighborhoods** — Livability intelligence (walk score, schools, crime, amenities)
- 📉 **Market History** — Monthly price trends, heatmap, and 6-month linear forecast
- 💼 **Portfolio** — Session-based investment portfolio with mortgage & cash flow modelling

### Authentication
Currently open for development. JWT authentication will be added before production launch.
""",
    version="1.2.0",
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
    expose_headers=["X-Request-ID", "X-Process-Time"],
)


# ── Request ID + Timing Middleware ─────────────────────────────────────────────
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Attach a unique X-Request-ID and X-Process-Time to every response."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{elapsed_ms}ms"
    return response


# ── Global Error Handlers ─────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return a structured JSON error."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later.",
            "detail": str(exc) if settings.debug else None,
        },
    )


# ── Routers ────────────────────────────────────────────────────────────────────
# ── Existing routers ──────────────────────────────────────────────────────────
app.include_router(properties.router, prefix=settings.api_v1_prefix)
app.include_router(analytics.router, prefix=settings.api_v1_prefix)
app.include_router(waitlist.router, prefix=settings.api_v1_prefix)
app.include_router(stats.router, prefix=settings.api_v1_prefix)
app.include_router(search.router, prefix=settings.api_v1_prefix)
app.include_router(contact.router, prefix=settings.api_v1_prefix)
app.include_router(favorites.router, prefix=settings.api_v1_prefix)
app.include_router(compare.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)

# ── New domain routers ─────────────────────────────────────────────────────────
app.include_router(reviews.router, prefix=settings.api_v1_prefix)
app.include_router(neighborhoods.router, prefix=settings.api_v1_prefix)
app.include_router(market.router, prefix=settings.api_v1_prefix)
app.include_router(portfolio.router, prefix=settings.api_v1_prefix)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="API health check")
async def health_check():
    """Returns the current health and version of the API."""
    return {
        "status": "healthy",
        "version": "1.2.0",
        "environment": settings.environment,
        "database": "connected",
        "project": settings.project_name,
        "domains": [
            "properties", "analytics", "search", "stats", "favorites",
            "compare", "contact", "waitlist", "admin",
            "reviews", "neighborhoods", "market", "portfolio",
        ],
    }


@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    return JSONResponse({
        "message": "Welcome to the Aurevia API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "version": "1.2.0",
    })

