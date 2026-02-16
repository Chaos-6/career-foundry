"""
Behavioral Interview Answer Evaluator — FastAPI Application

This is the entry point for the backend. It:
1. Creates the FastAPI app instance
2. Configures CORS (so the React frontend can talk to us)
3. Registers route handlers
4. Sets up startup/shutdown lifecycle events

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.rate_limit import RateLimitMiddleware

# IMPORTANT: Import models so SQLAlchemy registers them with Base.metadata
# before init_db() calls create_all(). Without this, no tables get created.
import app.models  # noqa: F401
from app.routers import (
    answers,
    auth,
    billing,
    coaching,
    companies,
    dashboard,
    evaluations,
    generator,
    mock_interview,
    oauth,
    questions,
    scenarios,
    templates,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic.

    Code before 'yield' runs on startup.
    Code after 'yield' runs on shutdown.
    """
    # --- Startup ---
    print("🚀 Starting Behavioral Interview Answer Evaluator API...")
    await init_db()
    print("✅ Database tables created/verified")

    yield  # App is running, handling requests

    # --- Shutdown ---
    print("👋 Shutting down...")


app = FastAPI(
    title="Behavioral Interview Answer Evaluator API",
    description="AI-powered STAR answer coaching for tech job seekers",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS Middleware ---
# Without this, the React app (localhost:3000) can't call the API (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate Limiting Middleware ---
# Global per-IP limit: 100 requests/min for all endpoints.
# Expensive endpoints (evaluations, generation) get tighter per-route limits
# via the rate_limit() dependency in their routers.
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)


# --- Register Routers ---
app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(billing.router)
app.include_router(companies.router)
app.include_router(questions.router)
app.include_router(answers.router)
app.include_router(evaluations.router)
app.include_router(dashboard.router)
app.include_router(mock_interview.router)
app.include_router(generator.router)
app.include_router(coaching.router)
app.include_router(templates.router)
app.include_router(scenarios.router)


# --- Health Check Endpoints ---

@app.get("/", tags=["health"])
async def root():
    """Root endpoint — confirms the API is alive."""
    return {
        "service": "Behavioral Interview Answer Evaluator",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Detailed health check — verifies database connectivity."""
    from sqlalchemy import text

    from app.database import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "environment": settings.APP_ENV,
    }
