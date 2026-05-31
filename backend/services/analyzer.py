"""
Static code analyzer service.

Performs heuristic-based analysis on source files without executing them.
All checks are language-agnostic unless explicitly noted.

Detected issue types:
  - large_file      : file exceeds 300 lines
  - large_function  : function exceeds 50 lines (Python, JS/TS)
  - deep_nesting    : indentation depth >= 4 levels
  - long_line       : line exceeds 120 characters
  - todo_comment    : unresolved TODO/FIXME/HACK/XXX marker
  - magic_number    : numeric literal not assigned to a named constant
  - print_statement : print() call in Python code (debug artifact)
"""

import re
import logging
from typing import List

from models.schemas import FileContent, Issue, Severity

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

MAX_FILE_LINES = 300
MAX_FUNCTION_LINES = 50
MAX_LINE_LENGTH = 120
MAX_NESTING_DEPTH = 4  # number of indent levels (assumes 4-space or 2-space indent)

# Languages where function-level analysis is applicable
FUNCTION_AWARE_LANGUAGES = {"python", "javascript", "typescript", "go", "java", "ruby", "php"}


# ─── Public Entry Point ───────────────────────────────────────────────────────


def analyze_files(files: List[FileContent]) -> List[Issue]:
    """
    Run all checks on each file and return a flat list of detected issues.
    Issues are sorted: critical → warning → info, then by file path.
    """
    all_issues: List[Issue] = []
    for file in files:
        file_issues = _analyze_file(file)
        all_issues.extend(file_issues)
        logger.debug(f"  {file.path}: {len(file_issues)} issues")

    # Sort for consistent, readable output
    severity_order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
    all_issues.sort(key=lambda i: (severity_order[i.severity], i.file, i.line or 0))

    logger.info(f"Analysis complete: {len(all_issues)} total issues across {len(files)} files")
    return all_issues


def calculate_score(issues: List[Issue]) -> int:
    """
    Compute a quality score from 0–100 based on detected issues.

    Penalty per issue (capped per severity to prevent single bad files from
    tanking an otherwise healthy codebase):
      critical : -10, capped at -40
      warning  : -5,  capped at -30
      info     : -1,  capped at -10
    """
    penalties = {Severity.CRITICAL: 10, Severity.WARNING: 5, Severity.INFO: 1}
    caps = {Severity.CRITICAL: 40, Severity.WARNING: 30, Severity.INFO: 10}

    deductions: dict[Severity, int] = {s: 0 for s in Severity}
    for issue in issues:
        sev = issue.severity
        if deductions[sev] < caps[sev]:
            deductions[sev] += penalties[sev]

    total = sum(deductions.values())
    return max(0, 100 - total)


# ─── Per-File Analysis ────────────────────────────────────────────────────────


def _analyze_file(file: FileContent) -> List[Issue]:
    issues: List[Issue] = []
    lines = file.content.splitlines()

    # ── File-level checks ──────────────────────────────────────────────────
    if len(lines) > MAX_FILE_LINES:
        issues.append(
            Issue(
                file=file.path,
                line=None,
                type="large_file",
                severity=Severity.WARNING,
                message=(
                    f"File has {len(lines)} lines (limit: {MAX_FILE_LINES}). "
                    "Consider splitting by responsibility into smaller modules."
                ),
            )
        )

    # ── Line-level checks ──────────────────────────────────────────────────
    for lineno, line in enumerate(lines, start=1):
        # Long lines
        if len(line) > MAX_LINE_LENGTH:
            issues.append(
                Issue(
                    file=file.path,
                    line=lineno,
                    type="long_line",
                    severity=Severity.INFO,
                    message=f"Line is {len(line)} characters (limit: {MAX_LINE_LENGTH}).",
                )
            )

        # TODO / FIXME / unresolved markers
        marker_match = re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.IGNORECASE)
        if marker_match:
            snippet = line.strip()[:80]
            issues.append(
                Issue(
                    file=file.path,
                    line=lineno,
                    type="todo_comment",
                    severity=Severity.INFO,
                    message=f"Unresolved marker '{marker_match.group(1)}': {snippet}",
                )
            )

        # Python-specific: print() left in production code
        if file.language == "python" and re.match(r"^\s*print\s*\(", line):
            issues.append(
                Issue(
                    file=file.path,
                    line=lineno,
                    type="print_statement",
                    severity=Severity.INFO,
                    message="print() call detected. Use a logger for production code.",
                )
            )

    # ── Structural checks (require language awareness) ─────────────────────
    if file.language in FUNCTION_AWARE_LANGUAGES:
        issues.extend(_check_function_lengths(file, lines))

    issues.extend(_check_nesting_depth(file, lines))
    issues.extend(_check_magic_numbers(file, lines))

    return issues


# ─── Structural Checks ────────────────────────────────────────────────────────


def _check_function_lengths(file: FileContent, lines: List[str]) -> List[Issue]:
    """
    Detect functions that exceed MAX_FUNCTION_LINES.
    Supports Python (def), JavaScript/TypeScript (function keyword + arrow functions),
    Go (func), Java/C# methods, and Ruby (def).
    """
    issues: List[Issue] = []

    # Language-specific patterns to detect function/method declarations
    if file.language == "python":
        func_re = re.compile(r"^\s*(async\s+)?def\s+(\w+)\s*\(")
    elif file.language in ("javascript", "typescript"):
        func_re = re.compile(
            r"(?:function\s+(\w+)\s*\(|"            # named function
            r"(\w+)\s*(?::\s*\w+\s*)?=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))"  # assigned
        )
    elif file.language == "go":
        func_re = re.compile(r"^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(")
    elif file.language in ("java", "csharp"):
        func_re = re.compile(
            r"(?:public|private|protected|static|async|override|virtual)[\w\s<>\[\]]*"
            r"\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+\s*)?\{"
        )
    elif file.language == "ruby":
        func_re = re.compile(r"^\s*def\s+(\w+)")
    else:
        return []

    func_start: int | None = None
    func_name: str = "anonymous"

    for lineno, line in enumerate(lines, start=1):
        match = func_re.search(line)
        if match:
            # Close the previous function we were tracking
            if func_start is not None:
                length = lineno - func_start
                if length > MAX_FUNCTION_LINES:
                    issues.append(
                        Issue(
                            file=file.path,
                            line=func_start,
                            type="large_function",
                            severity=Severity.WARNING,
                            message=(
                                f"Function '{func_name}' is {length} lines long "
                                f"(limit: {MAX_FUNCTION_LINES}). "
                                "Consider extracting sub-routines."
                            ),
                        )
                    )
            func_start = lineno
            # Try to extract the function name from whichever capture group matched
            func_name = next(
                (g for g in match.groups() if g and g.strip()), "anonymous"
            )

    # Handle the last function in the file
    if func_start is not None:
        length = len(lines) - func_start + 1
        if length > MAX_FUNCTION_LINES:
            issues.append(
                Issue(
                    file=file.path,
                    line=func_start,
                    type="large_function",
                    severity=Severity.WARNING,
                    message=(
                        f"Function '{func_name}' is {length} lines long "
                        f"(limit: {MAX_FUNCTION_LINES}). "
                        "Consider extracting sub-routines."
                    ),
                )
            )

    return issues


def _check_nesting_depth(file: FileContent, lines: List[str]) -> List[Issue]:
    """
    Flag lines with indentation representing >= MAX_NESTING_DEPTH nested blocks.
    Heuristic: assumes 4-space or 2-space indentation (takes the minimum found).
    """
    issues: List[Issue] = []
    reported: set[int] = set()

    # Detect the project's indent size from the first indented line
    indent_size = 4
    for line in lines:
        stripped = line.lstrip()
        if stripped and line != stripped:
            indent = len(line) - len(stripped)
            if indent in (2, 4):
                indent_size = indent
                break

    for lineno, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if not stripped or stripped.startswith(("#", "//", "/*", "*")):
            continue

        indent = len(line) - len(stripped)
        depth = indent // indent_size

        if depth >= MAX_NESTING_DEPTH and lineno not in reported:
            issues.append(
                Issue(
                    file=file.path,
                    line=lineno,
                    type="deep_nesting",
                    severity=Severity.WARNING,
                    message=(
                        f"Nesting depth {depth} detected (limit: {MAX_NESTING_DEPTH}). "
                        "Use early returns or extract helper functions to flatten this code."
                    ),
                )
            )
            reported.add(lineno)

    return issues


def _check_magic_numbers(file: FileContent, lines: List[str]) -> List[Issue]:
    """
    Detect numeric literals used directly in expressions rather than named constants.
    Ignores: 0, 1, -1 (universally understood), constant assignments (ALL_CAPS = 42),
    and lines that are comments or string literals.
    """
    issues: List[Issue] = []

    # Matches integers >= 2 and floats not adjacent to identifiers
    magic_re = re.compile(
        r"(?<![.\w])(?<!\w)"         # not after a dot or word char
        r"(?!0[xXbBoO])"             # not hex/binary/octal prefixes
        r"(\b[2-9]\d+\b|\b\d{3,}\b)" # 2+ digits or 3+ digit numbers
        r"(?!\s*[=:,])"              # not on the right side of an assignment
    )

    # Pattern for constant definitions — we skip these lines
    constant_assign_re = re.compile(r"^[A-Z_][A-Z0-9_]*\s*=")

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Skip comments, blank lines, and import statements
        if not stripped:
            continue
        if stripped.startswith(("#", "//", "/*", "*", "import ", "from ", "use ", "require(")):
            continue
        # Skip string-only lines (quoted literals)
        if stripped.startswith(('"', "'", "`")):
            continue
        # Skip constant assignments (e.g., MAX_SIZE = 1024)
        if constant_assign_re.match(stripped):
            continue

        magic_numbers = magic_re.findall(line)
        if magic_numbers:
            unique = sorted(set(magic_numbers))
            issues.append(
                Issue(
                    file=file.path,
                    line=lineno,
                    type="magic_number",
                    severity=Severity.INFO,
                    message=(
                        f"Magic number(s) found: {', '.join(unique)}. "
                        "Replace with named constants for clarity and maintainability."
                    ),
                )
            )

    return issues
