"""
Shared utility functions: language detection, path filtering, and stat calculation.
These are pure functions with no dependencies on other project modules.
"""

from collections import Counter
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from models.schemas import FileContent, LanguageStats

# ─── Language Detection ───────────────────────────────────────────────────────

# Maps file extensions to language names used throughout the app
LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".java": "java",
    ".rb": "ruby",
    ".rs": "rust",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".sh": "bash",
    ".bash": "bash",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".sql": "sql",
}

# ─── Path Filtering ───────────────────────────────────────────────────────────

# Directories that should never be analyzed (dependencies, build outputs, etc.)
SKIP_DIRS: set[str] = {
    "node_modules",
    ".git",
    "__pycache__",
    "dist",
    "build",
    "vendor",
    ".venv",
    "venv",
    ".next",
    ".nuxt",
    "out",
    "target",
    "pkg",
    "coverage",
    ".cache",
    "tmp",
    "temp",
    ".idea",
    ".vscode",
}

# File extensions that are binary or auto-generated — skip entirely
SKIP_EXTENSIONS: set[str] = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".webp",
    ".mp4",
    ".mp3",
    ".wav",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".pyc",
    ".pyo",
    ".wasm",
    ".lock",
    ".sum",
}


def detect_language(path: str) -> str:
    """Return the language name for a file path based on its extension."""
    ext = PurePosixPath(path).suffix.lower()
    return LANGUAGE_MAP.get(ext, "unknown")


def should_skip_path(path: str) -> bool:
    """
    Return True if a file should be excluded from analysis.
    Skips: vendor dirs, dot-hidden dirs, binary extensions, minified files.
    """
    parts = PurePosixPath(path).parts

    # Skip any file that lives inside a vendor/build directory
    for part in parts[:-1]:
        if part in SKIP_DIRS:
            return True
        # Also skip dot-hidden directories (e.g. .git, .vscode) except .github
        if part.startswith(".") and part not in (".github",):
            return True

    # Skip by file extension (binaries, lock files, etc.)
    ext = PurePosixPath(path).suffix.lower()
    if ext in SKIP_EXTENSIONS:
        return True

    # Skip minified files (e.g. bundle.min.js)
    filename = parts[-1] if parts else ""
    if ".min." in filename:
        return True

    return False


# ─── Statistics ───────────────────────────────────────────────────────────────


def calculate_language_breakdown(files: "List[FileContent]") -> "List[LanguageStats]":
    """
    Return a sorted list of language distribution stats.
    Imported inline to avoid circular imports at module load time.
    """
    from models.schemas import LanguageStats

    counts = Counter(f.language for f in files)
    total = len(files)

    if total == 0:
        return []

    return [
        LanguageStats(
            language=lang,
            file_count=count,
            percentage=round(count / total * 100, 1),
        )
        for lang, count in counts.most_common()
    ]
