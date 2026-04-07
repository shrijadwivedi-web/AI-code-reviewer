"""
POST /analyze-pr

Orchestrates:
  1. Fetch changed files (with diffs) from a GitHub pull request
  2. Run static analysis on the diff content
  3. Call AI for suggestions
  4. Return a scored AnalysisResult scoped to the PR changes
"""

import logging

from fastapi import APIRouter, HTTPException

from models.schemas import (
    AnalysisResult,
    AnalysisType,
    AnalyzePRRequest,
    Severity,
)
from services.ai_service import get_ai_suggestions
from services.analyzer import analyze_files, calculate_score
from services.github_service import fetch_pr_files
from utils.helpers import calculate_language_breakdown

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/analyze-pr",
    response_model=AnalysisResult,
    summary="Analyze a GitHub pull request",
    description=(
        "Fetches changed files from a pull request, runs static analysis on the diff, "
        "and returns AI-generated improvement suggestions with a quality score."
    ),
)
async def analyze_pr(request: AnalyzePRRequest) -> AnalysisResult:
    logger.info(f"PR analysis requested: {request.pr_url}")

    # ── Step 1: Fetch PR diff files ────────────────────────────────────────
    try:
        files = await fetch_pr_files(request.pr_url, request.github_token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception(f"Unexpected error fetching PR: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Failed to connect to GitHub. Please try again shortly.",
        )

    # ── Step 2: Static analysis ────────────────────────────────────────────
    issues = analyze_files(files)
    score = calculate_score(issues)

    # ── Step 3: AI suggestions ─────────────────────────────────────────────
    suggestions = await get_ai_suggestions(files, issues)

    # ── Step 4: Assemble result ────────────────────────────────────────────
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
        f"PR analysis complete — score: {score}, "
        f"changed files: {len(files)}, issues: {len(issues)}, suggestions: {len(suggestions)}"
    )

    return AnalysisResult(
        score=score,
        summary=summary,
        issues=issues,
        suggestions=suggestions,
        file_count=len(files),
        analyzed_file_count=len(files),
        language_breakdown=language_breakdown,
        analysis_type=AnalysisType.PR,
    )


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
        f"Analyzed {file_count} changed file{'s' if file_count != 1 else ''} in this PR. "
        f"Code quality is {quality} (score: {score}/100). "
        f"Found {critical} critical issue{'s' if critical != 1 else ''} and "
        f"{warnings} warning{'s' if warnings != 1 else ''}. "
        f"Generated {suggestion_count} AI-powered suggestion{'s' if suggestion_count != 1 else ''}."
    )
