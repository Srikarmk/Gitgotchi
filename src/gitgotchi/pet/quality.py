"""Commit quality scoring."""
import re
from typing import Iterable

HUGE_COMMIT_LINES = 500

# How far a single commit moves the running quality score (0-1).
SMOOTHING = 0.35

VAGUE_SUBJECTS = {
    "fix bug",
    "fix bugs",
    "fix stuff",
    "fix things",
    "small fix",
    "minor fix",
    "minor changes",
    "small changes",
    "some changes",
    "more changes",
    "update code",
    "update files",
    "work in progress",
}

CONVENTIONAL_COMMIT = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|tests|build|ci|chore|revert)"
    r"(\([^)]*\))?!?: \S"
)

TEST_FILE = re.compile(
    r"(^|/)(tests?|__tests__|spec)/"
    r"|(^|/)test_[^/]+$"
    r"|_test\.[^/]+$"
    r"|\.(test|spec)\.[^/]+$"
)


def commit_subject(message: str) -> str:
    """First line of a commit message."""
    lines = message.strip().splitlines()
    return lines[0].strip() if lines else ""


def is_vague(subject: str) -> bool:
    """True for messages like "fix", "wip" or "update code"."""
    normalized = subject.lower().strip(" .!")
    return len(normalized.split()) <= 1 or normalized in VAGUE_SUBJECTS


def is_test_file(path: str) -> bool:
    return bool(TEST_FILE.search(path.replace("\\", "/")))


def score_commit(
    message: str,
    lines_changed: int,
    files: Iterable[str] = (),
    is_revert: bool = False,
) -> float:
    """Score a single commit from 0 to 100 (50 is neutral).

    - descriptive message: +15
    - conventional commit prefix (feat:, fix: ...): +5
    - touches tests: +10
    - reasonable size: +5
    - vague message: -30
    - huge commit (>500 lines): -15
    - revert: -10
    """
    subject = commit_subject(message)
    score = 50.0

    if is_vague(subject):
        score -= 30
    elif len(subject) >= 15 and len(subject.split()) >= 3:
        score += 15

    if CONVENTIONAL_COMMIT.match(subject):
        score += 5

    if any(is_test_file(f) for f in files):
        score += 10

    if lines_changed > HUGE_COMMIT_LINES:
        score -= 15
    elif lines_changed > 0:
        score += 5

    if is_revert:
        score -= 10

    return max(0.0, min(100.0, score))


def update_quality(current: float, commit_score: float) -> float:
    """Blend a commit's score into the running quality score."""
    return current + SMOOTHING * (commit_score - current)
