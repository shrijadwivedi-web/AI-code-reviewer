"""
Pydantic schemas for the AI Code Reviewer API.
All request/response models are defined here to ensure a single source of truth.
"""

import re
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, field_validator, Field


# ─── Enums ────────────────────────────────────────────────────────────────────


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AnalysisType(str, Enum):
    REPO = "repo"
    PR = "pr"


# ─── Internal Models (not exposed in API responses) ──────────────────────────


class FileContent(BaseModel):
    """Represents a fetched source file ready for analysis."""

    path: str
    content: str
    language: str
    size: int  # bytes


# ─── API Response Models ──────────────────────────────────────────────────────


class Issue(BaseModel):
    """A single code quality issue detected during static analysis."""

    file: str
    line: Optional[int] = None
    type: str  # e.g. "large_function", "deep_nesting", "magic_number"
    severity: Severity
    message: str


class Suggestion(BaseModel):
    """An AI-generated improvement suggestion."""

    file: str
    category: str
    severity: Severity
    suggestion: str
    example: Optional[str] = None  # short code snippet demonstrating the fix


class LanguageStats(BaseModel):
    """Language distribution stats for a repository."""

    language: str
    file_count: int
    percentage: float


class AnalysisResult(BaseModel):
    """The complete result returned to the frontend after analysis."""

    score: int  # 0–100
    summary: str
    issues: List[Issue]
    suggestions: List[Suggestion]
    file_count: int
    analyzed_file_count: int
    language_breakdown: List[LanguageStats]
    analysis_type: AnalysisType = AnalysisType.REPO


# ─── API Request Models ───────────────────────────────────────────────────────


class AnalyzeRepoRequest(BaseModel):
    """Request body for POST /analyze-repo."""

    repo_url: str = Field(..., max_length=200)
    github_token: Optional[str] = Field(None, max_length=100)

    @field_validator("repo_url")
    @classmethod
    def validate_repo_url(cls, v: str) -> str:
        v = v.strip()
        # Strictly match github.com/owner/repo
        pattern = r"^https?://(www\.)?github\.com/[\w-]+/[\w.-]+/?$"
        if not re.match(pattern, v):
            raise ValueError("URL must be a valid GitHub repository URL (e.g., https://github.com/owner/repo).")
        return v


class AnalyzePRRequest(BaseModel):
    """Request body for POST /analyze-pr."""

    pr_url: str = Field(..., max_length=300)
    github_token: Optional[str] = Field(None, max_length=100)

    @field_validator("pr_url")
    @classmethod
    def validate_pr_url(cls, v: str) -> str:
        v = v.strip()
        # Strictly match github.com/owner/repo/pull/123
        pattern = r"^https?://(www\.)?github\.com/[\w-]+/[\w.-]+/pull/\d+/?$"
        if not re.match(pattern, v):
            raise ValueError("URL must be a valid GitHub pull request URL (e.g., https://github.com/owner/repo/pull/1).")
        return v
