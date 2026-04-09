"""
AI Code Reviewer — FastAPI application entry point.

Startup checklist:
  - Loads environment variables from .env
  - Configures structured logging
  - Registers CORS middleware (allows frontend dev server)
  - Mounts /api routers for repo and PR analysis
  - Exposes /health for uptime monitoring
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import pr, repo

# Load .env before anything else reads os.getenv()
load_dotenv()

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks."""
    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))
    github_token_configured = bool(os.getenv("GITHUB_TOKEN"))

    logger.info("=" * 60)
    logger.info("AI Code Reviewer API starting up")
    logger.info(f"  Gemini AI  : {'✓ configured' if gemini_configured else '✗ not set (fallback mode)'}")
    logger.info(f"  GitHub token: {'✓ configured' if github_token_configured else '✗ not set (rate limits apply)'}")
    logger.info("=" * 60)

    yield  # Application runs here

    logger.info("AI Code Reviewer API shutting down.")


# ─── Application ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Code Reviewer API",
    description=(
        "Analyze GitHub repositories and pull requests for code quality issues. "
        "Returns a quality score, detected issues, and AI-powered improvement suggestions."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Flattens complex Pydantic errors into a single readable message for the frontend."""
    # Grab the first validation failure (usually the most relevant)
    first_error = exc.errors()[0]
    field_name = first_error.get("loc", ["Unknown"])[-1]
    error_msg = first_error.get("msg", "Invalid input")
    
    user_friendly_message = f"Check your input for '{field_name}': {error_msg}"
    
    return JSONResponse(
        status_code=422,
        content={"detail": user_friendly_message}
    )

# ─── CORS ─────────────────────────────────────────────────────────────────────

# Allow both the Vite dev server and any production frontend origin
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
allowed_origins = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(repo.router, prefix="/api", tags=["Repository Analysis"])
app.include_router(pr.router, prefix="/api", tags=["PR Analysis"])


# ─── Health Check ─────────────────────────────────────────────────────────────


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check() -> dict:
    """Returns 200 OK when the service is running. Used by uptime monitors."""
    return {
        "status": "ok",
        "service": "ai-code-reviewer",
        "version": "1.0.0",
    }
