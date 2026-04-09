"""
POST /analyze-repo

Orchestrates:
  1. Fetch repository files from GitHub
  2. Run static analysis
  3. Call AI for suggestions
  4. Return a scored AnalysisResult
"""

import logging
import time

from fastapi import APIRouter, HTTPException

from models.schemas import (
    AnalysisResult,
    AnalysisType,
    AnalyzeRepoRequest,
    Severity,
)
from services.ai_service import get_ai_suggestions
from services.analyzer import analyze_files, calculate_score
from services.github_service import fetch_repo_files
from utils.helpers import calculate_language_breakdown

router = APIRouter()
logger = logging.getLogger(__name__)

# Simple in-memory TTL Cache (Key: url + token, Value: tuple(timestamp, AnalysisResult))
CACHE_TTL_SECONDS = 3600 # 1 hour
_analysis_cache = {}


@router.post(
    "/analyze-repo",
    response_model=AnalysisResult,
    summary="Analyze a GitHub repository",
    description=(
        "Fetches public repository files, runs static analysis, "
        "and returns AI-generated improvement suggestions with a quality score."
    ),
)
async def analyze_repo(request: AnalyzeRepoRequest) -> AnalysisResult:
    logger.info(f"Repository analysis requested: {request.repo_url}")

    # ── Cache Check ────────────────────────────────────────────────────────
    cache_key = f"{request.repo_url}::{request.github_token or 'anon'}"
    if cache_key in _analysis_cache:
        cached_time, cached_result = _analysis_cache[cache_key]
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            logger.info("Serving analysis from cache.")
            return cached_result

    # ── Step 1: Fetch source files ─────────────────────────────────────────
    try:
        files = await fetch_repo_files(request.repo_url, request.github_token)
    except ValueError as exc:
        # User-facing errors (bad URL, 404, rate limit)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception(f"Unexpected error fetching repo: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Failed to connect to GitHub. Please try again shortly.",
        )

    # ── Step 2: Static analysis ────────────────────────────────────────────
    issues = analyze_files(files)
    score = calculate_score(issues)

    # ── Step 3: AI suggestions ─────────────────────────────────────────────
    suggestions = await get_ai_suggestions(files, issues)

    # ── Step 4: Assemble result ───────────────────────────────────────────
    language_breakdown = calculate_language_breakdown(files)

    critical_count = sum(1 for i in issues if i.severity == Severity.CRITICAL)
    warning_count = sum(1 for i in issues if i.severity == Severity.WARNING)

    summary = _build_summary(
        score=score,
        file_count=len(files),
        critical=critical_count,
        warnings=warning_count,
        suggestion_count=len(suggestions),
    )

    logger.info(
        f"Repo analysis complete — score: {score}, "
        f"files: {len(files)}, issues: {len(issues)}, suggestions: {len(suggestions)}"
    )

    final_result = AnalysisResult(
        score=score,
        summary=summary,
        issues=issues,
        suggestions=suggestions,
        file_count=len(files),
        analyzed_file_count=len(files),
        language_breakdown=language_breakdown,
        analysis_type=AnalysisType.REPO,
    )
    _analysis_cache[cache_key] = (time.time(), final_result)
    return final_result


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _build_summary(
    score: int,
    file_count: int,
    critical: int,
    warnings: int,
    suggestion_count: int,
) -> str:
    if score >= 85:
        quality = "excellent"
    elif score >= 70:
        quality = "good"
    elif score >= 50:
        quality = "moderate — room for improvement"
    else:
        quality = "needs significant improvement"

    return (
        f"Analyzed {file_count} files. "
        f"Overall code quality is {quality} (score: {score}/100). "
        f"Found {critical} critical issue{'s' if critical != 1 else ''} and "
        f"{warnings} warning{'s' if warnings != 1 else ''}. "
        f"Generated {suggestion_count} AI-powered suggestion{'s' if suggestion_count != 1 else ''}."
    )
