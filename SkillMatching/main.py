"""
main.py
-------
FastAPI application entry point for the RADIX Talent Match – ATS Skill Matching Module.

Run with:
    uvicorn main:app --reload --port 8000

Swagger UI:
    http://localhost:8000/docs

ReDoc:
    http://localhost:8000/redoc
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.ats import router as ats_router, _load_jds_from_disk
import routes.ats as ats_module

# ──────────────────────────────────────────────────────────────────────────────
# Logging configuration
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Startup / Shutdown lifecycle
# ──────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: pre-load and cache all JDs from disk
    logger.info("Loading JDs from disk...")
    ats_module._cached_jds = _load_jds_from_disk()
    logger.info("Loaded %d JDs. Server ready.", len(ats_module._cached_jds))
    yield
    # SHUTDOWN
    logger.info("ATS server shutting down.")


# ──────────────────────────────────────────────────────────────────────────────
# App
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="RADIX Talent Match – ATS Skill Matching API",
    description=(
        "Role 5 – Skill Matching Module for the RADIX Talent Match Hackathon.\n\n"
        "Compares candidate resumes against Job Descriptions and returns:\n"
        "- Match Score (0–100%)\n"
        "- Matched Skills\n"
        "- Missing Skills\n"
        "- Partial Matches\n"
        "- Ranked Job Recommendations\n"
        "- Learning Suggestions\n\n"
        "**Teammate Integration**: Use `POST /ats/match-from-json` to send "
        "candidate skills directly as JSON from your module."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────────────────────────────────────
# CORS — allow all origins during hackathon (tighten for production)
# ──────────────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────────────────────────────────────
app.include_router(ats_router)


# ──────────────────────────────────────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "RADIX ATS Skill Matching",
        "version": "1.0.0",
        "status": "running",
        "jds_loaded": len(ats_module._cached_jds),
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "jds_available": len(ats_module._cached_jds)}
