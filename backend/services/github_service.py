"""
GitHub API integration service.

Responsibilities:
  - Parse GitHub repo and PR URLs
  - Fetch repository file trees and content via PyGithub
  - Fetch changed files (with diffs) from pull requests
  - Enforce file limits and skip non-analyzable paths
"""

import asyncio
import base64
import logging
import re
from typing import List, Optional

from github import Github, GithubException

from models.schemas import FileContent
from utils.helpers import detect_language, should_skip_path

logger = logging.getLogger(__name__)

# Safety limits to prevent excessive API usage on large repos
MAX_FILES = 50
MAX_FILE_SIZE_BYTES = 150_000  # 150 KB — skip unusually large single files


# ─── URL Parsing ──────────────────────────────────────────────────────────────


def parse_repo_url(url: str) -> tuple[str, str]:
    """
    Extract (owner, repo_name) from a GitHub URL.
    Supports formats:
      https://github.com/owner/repo
      https://github.com/owner/repo.git
      git@github.com:owner/repo.git
    """
    pattern = r"github\.com[/:]([^/\s]+)/([^/.\s]+?)(?:\.git)?$"
    match = re.search(pattern, url.strip())
    if not match:
        raise ValueError(
            f"Could not parse repository URL: '{url}'. "
            "Expected format: https://github.com/owner/repo"
        )
    return match.group(1), match.group(2)


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """
    Extract (owner, repo_name, pr_number) from a GitHub PR URL.
    Expected format: https://github.com/owner/repo/pull/123
    """
    pattern = r"github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)"
    match = re.search(pattern, url.strip())
    if not match:
        raise ValueError(
            f"Could not parse PR URL: '{url}'. "
            "Expected format: https://github.com/owner/repo/pull/123"
        )
    return match.group(1), match.group(2), int(match.group(3))


# ─── Repository File Fetching ─────────────────────────────────────────────────


async def fetch_repo_files(
    repo_url: str, token: Optional[str] = None
) -> List[FileContent]:
    """
    Async wrapper: fetches analyzable files from a public GitHub repo.
    Runs the synchronous PyGithub calls in a thread pool to avoid blocking.
    """
    return await asyncio.to_thread(_fetch_repo_files_sync, repo_url, token)


def _fetch_repo_files_sync(
    repo_url: str, token: Optional[str]
) -> List[FileContent]:
    """Synchronous implementation of repository file fetching."""
    owner, repo_name = parse_repo_url(repo_url)
    g = Github(token) if token else Github()

    try:
        repo = g.get_repo(f"{owner}/{repo_name}")
    except GithubException as e:
        if e.status == 404:
            raise ValueError(f"Repository not found: '{owner}/{repo_name}'. Is it public?")
        if e.status == 403:
            raise ValueError(
                "GitHub API rate limit exceeded. "
                "Please provide a GitHub Personal Access Token to increase the limit."
            )
        raise ValueError(f"GitHub API error ({e.status}): {e.data.get('message', 'Unknown error')}")

    logger.info(f"Fetching file tree for {owner}/{repo_name} (branch: {repo.default_branch})")

    try:
        tree = repo.get_git_tree(sha=repo.default_branch, recursive=True)
    except GithubException:
        raise ValueError(
            f"Could not fetch file tree for '{owner}/{repo_name}'. "
            "The repository may be empty or use an unsupported branch structure."
        )

    # Filter the tree to only analyzable files
    candidate_paths = []
    for item in tree.tree:
        if item.type != "blob":
            continue
        if should_skip_path(item.path):
            continue
        if detect_language(item.path) == "unknown":
            continue
        if item.size and item.size > MAX_FILE_SIZE_BYTES:
            logger.debug(f"Skipping large file: {item.path} ({item.size} bytes)")
            continue
        candidate_paths.append(item.path)

    if not candidate_paths:
        raise ValueError(
            "No analyzable source files found. "
            "The repository may contain only binary or unrecognized file types."
        )

    # Fetch content for up to MAX_FILES files
    files: List[FileContent] = []
    for path in candidate_paths[:MAX_FILES]:
        try:
            content_file = repo.get_contents(path)
            # get_contents can return a list for directories — guard against it
            if isinstance(content_file, list):
                continue

            if content_file.encoding == "base64":
                raw = base64.b64decode(content_file.content).decode("utf-8", errors="replace")
            else:
                raw = (content_file.decoded_content or b"").decode("utf-8", errors="replace")

            files.append(
                FileContent(
                    path=path,
                    content=raw,
                    language=detect_language(path),
                    size=content_file.size or 0,
                )
            )
        except GithubException as e:
            logger.warning(f"Could not fetch file '{path}': {e}")
            continue
        except UnicodeDecodeError:
            logger.debug(f"Skipping binary-like file: {path}")
            continue

    logger.info(
        f"Fetched {len(files)} files from {owner}/{repo_name} "
        f"(skipped {len(candidate_paths) - len(files)} files)"
    )
    return files


# ─── Pull Request File Fetching ───────────────────────────────────────────────


async def fetch_pr_files(
    pr_url: str, token: Optional[str] = None
) -> List[FileContent]:
    """
    Async wrapper: fetches changed files from a GitHub pull request.
    Uses the PR diff (patch) as the content so the analyzer reviews only the changes.
    """
    return await asyncio.to_thread(_fetch_pr_files_sync, pr_url, token)


def _fetch_pr_files_sync(
    pr_url: str, token: Optional[str]
) -> List[FileContent]:
    """Synchronous implementation of PR file fetching."""
    owner, repo_name, pr_number = parse_pr_url(pr_url)
    g = Github(token) if token else Github()

    try:
        repo = g.get_repo(f"{owner}/{repo_name}")
        pr = repo.get_pull(pr_number)
    except GithubException as e:
        if e.status == 404:
            raise ValueError(
                f"Pull request #{pr_number} not found in '{owner}/{repo_name}'. "
                "Check the URL and ensure the repository is public."
            )
        if e.status == 403:
            raise ValueError(
                "GitHub API rate limit exceeded. "
                "Please provide a GitHub Personal Access Token."
            )
        raise ValueError(f"GitHub API error ({e.status}): {e.data.get('message', 'Unknown error')}")

    logger.info(f"Fetching PR #{pr_number} files from {owner}/{repo_name}")

    files: List[FileContent] = []
    for pr_file in pr.get_files():
        if should_skip_path(pr_file.filename):
            continue
        if detect_language(pr_file.filename) == "unknown":
            continue
        if len(files) >= MAX_FILES:
            break

        # For PRs we analyze the diff patch, not the full file
        patch = pr_file.patch or ""
        if not patch.strip():
            logger.debug(f"Skipping file with empty patch: {pr_file.filename}")
            continue

        files.append(
            FileContent(
                path=pr_file.filename,
                content=patch,
                language=detect_language(pr_file.filename),
                size=len(patch.encode("utf-8")),
            )
        )

    logger.info(f"Fetched {len(files)} changed files from PR #{pr_number}")
    return files
