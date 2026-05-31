"""
AI suggestions service using Google Gemini.

Responsibilities:
  - Build a structured prompt from detected issues and code samples
  - Call the Gemini API and parse the JSON response
  - Fall back to rule-based suggestions if the API key is missing or the call fails

The AI is asked to return a strict JSON array so we can parse it reliably,
without needing fragile markdown/text extraction.
"""

import asyncio
import json
import logging
import os
import re
from typing import List, Optional

import google.generativeai as genai

from models.schemas import FileContent, Issue, Severity, Suggestion

logger = logging.getLogger(__name__)

# ─── Client Initialization ────────────────────────────────────────────────────

_model: Optional[genai.GenerativeModel] = None


def _get_model() -> Optional[genai.GenerativeModel]:
    """
    Lazily initialize the Gemini client.
    Returns None if GEMINI_API_KEY is not configured, allowing graceful fallback.
    """
    global _model
    if _model is not None:
        return _model

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set — AI suggestions will use fallback rules.")
        return None

    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,       # Low temp for consistent, structured output
            max_output_tokens=2048,
        ),
    )
    logger.info("Gemini model initialized (gemini-1.5-flash).")
    return _model


# ─── Public Interface ─────────────────────────────────────────────────────────


async def get_ai_suggestions(
    files: List[FileContent], issues: List[Issue]
) -> List[Suggestion]:
    """
    Generate AI-powered improvement suggestions for the detected issues.
    Falls back to static rule-based suggestions if AI is unavailable.
    """
    model = _get_model()
    if model is None:
        return _static_fallback_suggestions(issues)

    try:
        prompt = _build_prompt(files, issues)
        # Gemini's Python SDK is synchronous; run it off the event loop
        response = await asyncio.to_thread(model.generate_content, prompt)
        return _parse_response(response.text)
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}. Falling back to static suggestions.")
        return _static_fallback_suggestions(issues)


# ─── Prompt Engineering ───────────────────────────────────────────────────────


def _build_prompt(files: List[FileContent], issues: List[Issue]) -> str:
    """
    Construct a structured prompt that asks the model for JSON output only.

    Design choices:
      - Limit to top 15 issues to stay within token budgets
      - Include up to 5 file previews (30 lines each)
      - Explicitly forbid markdown in the response to make parsing reliable
    """
    # Summarise the top issues
    top_issues = issues[:15]
    issue_lines = "\n".join(
        f"  [{issue.severity.upper()}] {issue.file}"
        f"{':#' + str(issue.line) if issue.line else ''} "
        f"({issue.type}): {issue.message}"
        for issue in top_issues
    )

    # Brief code previews for context
    previews: List[str] = []
    for f in files[:5]:
        preview_lines = f.content.splitlines()[:30]
        preview = "\n".join(preview_lines)
        previews.append(f"### {f.path} ({f.language})\n```\n{preview}\n```")
    file_section = "\n\n".join(previews) if previews else "No code samples available."

    return f"""You are a senior software engineer performing a code review.

## Detected Issues
{issue_lines}

## Code Samples (first 30 lines per file)
{file_section}

## Instructions
Analyze the issues and code above and return ONLY a valid JSON array of improvement suggestions.
Do NOT include markdown code fences, explanations, or any text outside the JSON array.

Required JSON schema (each element):
{{
  "file": "path/to/file.py or 'general' if cross-cutting",
  "suggestion": "Specific, actionable suggestion (1-3 sentences)",
  "example": "Optional short code snippet (max 8 lines) or null"
}}

Rules:
- Provide 3 to 7 suggestions
- Be concrete, not generic ("Use logging" is good; "improve code" is not)
- Address the most impactful issues first
- Keep examples concise and directly relevant
- Return ONLY the JSON array, nothing else
"""


# ─── Response Parsing ─────────────────────────────────────────────────────────


def _parse_response(raw: str) -> List[Suggestion]:
    """
    Parse the model's response into Suggestion objects.
    Handles cases where the model wraps JSON in markdown code fences.
    """
    text = raw.strip()

    # Strip markdown code fences if present (e.g., ```json ... ```)
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()

    try:
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("Expected a JSON array at the top level.")
        suggestions = []
        for item in data:
            if isinstance(item, dict) and "file" in item and "suggestion" in item:
                suggestions.append(
                    Suggestion(
                        file=item["file"],
                        suggestion=item["suggestion"],
                        example=item.get("example"),
                    )
                )
        return suggestions
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse AI response as JSON: {e}\nRaw response:\n{raw[:500]}")
        return []


# ─── Static Fallback Suggestions ─────────────────────────────────────────────


def _static_fallback_suggestions(issues: List[Issue]) -> List[Suggestion]:
    """
    Rule-based suggestions used when the AI is unavailable.
    Maps issue types to pre-written, specific advice.
    """
    issue_types = {i.type for i in issues}
    suggestions: List[Suggestion] = []

    if "large_function" in issue_types:
        suggestions.append(
            Suggestion(
                file="general",
                suggestion=(
                    "Several functions exceed 50 lines. Apply the Single Responsibility Principle: "
                    "each function should do exactly one thing. Extract sub-routines into smaller, "
                    "descriptively named helpers."
                ),
                example=(
                    "# Instead of:\ndef process_order(order):\n    # 80 lines of validation, "
                    "pricing, and email logic\n\n"
                    "# Prefer:\ndef process_order(order):\n    validated = validate_order(order)\n"
                    "    total = calculate_total(validated)\n    notify_customer(validated, total)"
                ),
            )
        )

    if "deep_nesting" in issue_types:
        suggestions.append(
            Suggestion(
                file="general",
                suggestion=(
                    "Deep nesting (4+ levels) reduces readability and testability. "
                    "Use guard clauses (early returns) to invert nested conditions and flatten the flow."
                ),
                example=(
                    "# Before — deeply nested:\ndef handle(user, order):\n"
                    "    if user:\n        if order:\n            if order.valid:\n"
                    "                process(order)\n\n"
                    "# After — guard clauses:\ndef handle(user, order):\n"
                    "    if not user: return\n    if not order: return\n"
                    "    if not order.valid: return\n    process(order)"
                ),
            )
        )

    if "large_file" in issue_types:
        suggestions.append(
            Suggestion(
                file="general",
                suggestion=(
                    "Files over 300 lines typically mix multiple concerns. "
                    "Separate models, business logic, and utilities into distinct modules "
                    "following the Single Responsibility Principle."
                ),
                example=None,
            )
        )

    if "magic_number" in issue_types:
        suggestions.append(
            Suggestion(
                file="general",
                suggestion=(
                    "Replace magic numbers with named constants. This documents intent and "
                    "makes future changes safer — you only update one definition."
                ),
                example=(
                    "# Before:\nif retries > 3:\n    sleep(60)\n\n"
                    "# After:\nMAX_RETRIES = 3\nRETRY_DELAY_SECONDS = 60\n"
                    "if retries > MAX_RETRIES:\n    sleep(RETRY_DELAY_SECONDS)"
                ),
            )
        )

    if "todo_comment" in issue_types:
        suggestions.append(
            Suggestion(
                file="general",
                suggestion=(
                    "TODO/FIXME comments indicate incomplete work. Convert them into tracked "
                    "GitHub issues so they don't get lost in the codebase."
                ),
                example=None,
            )
        )

    if "print_statement" in issue_types:
        suggestions.append(
            Suggestion(
                file="general",
                suggestion=(
                    "Replace print() calls with Python's built-in logging module. "
                    "Loggers support log levels, timestamps, and can be silenced in production "
                    "without touching every print statement."
                ),
                example=(
                    "import logging\nlogger = logging.getLogger(__name__)\n\n"
                    "# Instead of: print('Processing order', order_id)\n"
                    "logger.info('Processing order %s', order_id)"
                ),
            )
        )

    # Always surface at least one suggestion
    if not suggestions:
        suggestions.append(
            Suggestion(
                file="general",
                suggestion=(
                    "The codebase looks clean! Consider adding type annotations and docstrings "
                    "to improve long-term maintainability and IDE support."
                ),
                example=None,
            )
        )

    return suggestions
