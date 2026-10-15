"""Dig spooky facts out of a repository's history for the séance."""
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from git import GitCommandError, Repo

from gitgotchi.history import HistoryCommit, read_history
from gitgotchi.pet.possession import detect_agent
from gitgotchi.pet.quality import commit_subject

TODO = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
MAX_BLAMES = 25


@dataclass
class Haunting:
    kind: str
    title: str
    detail: str
    when: Optional[datetime] = None
    facts: Dict[str, object] = field(default_factory=dict)

    def age_days(self) -> Optional[int]:
        return (datetime.now() - self.when).days if self.when else None


@dataclass
class Hauntings:
    items: List[Haunting] = field(default_factory=list)

    def by_kind(self) -> Dict[str, Haunting]:
        return {h.kind: h for h in self.items}

    def __bool__(self) -> bool:
        return bool(self.items)


def find_hauntings(repo: Repo, history: Optional[List[HistoryCommit]] = None) -> Hauntings:
    history = history if history is not None else read_history(repo)
    found = Hauntings()
    for finder in (_oldest_todo, _forgotten_file, _graveyard, _witching_hour, _first_spirit):
        try:
            haunting = finder(repo, history)
        except GitCommandError:
            haunting = None
        if haunting:
            found.items.append(haunting)
    return found


def _oldest_todo(repo: Repo, history) -> Optional[Haunting]:
    try:
        # Word boundaries are checked in Python; git's regex flavor varies by platform
        output = repo.git.grep("-n", "-I", "-E", "TODO|FIXME|HACK|XXX", "--", ".")
    except GitCommandError:  # no matches
        return None

    oldest = None
    candidates = []
    for line in output.splitlines():
        path, number, text = (line.split(":", 2) + ["", ""])[:3]
        if number.isdigit() and TODO.search(text):
            candidates.append((path, number, text))
    for path, number, text in candidates[:MAX_BLAMES]:
        blame = repo.git.blame("--line-porcelain", "-L", f"{number},{number}", "--", path)
        stamp = re.search(r"^author-time (\d+)", blame, re.MULTILINE)
        if not stamp:
            continue
        when = datetime.fromtimestamp(int(stamp.group(1)))
        if oldest is None or when < oldest[0]:
            oldest = (when, path, number, text.strip())

    if oldest is None:
        return None
    when, path, number, text = oldest
    match = TODO.search(text)
    note = text[match.start():] if match else text
    return Haunting(
        "todo",
        "The oldest unfinished business",
        f'{path}:{number}  "{note[:70]}"',
        when,
        {"path": path, "line": number, "note": note[:70]},
    )


def _forgotten_file(repo: Repo, history) -> Optional[Haunting]:
    tracked = set(repo.git.ls_files().splitlines())
    # (timestamp, position in history) so same-second commits keep their order
    last_touched: Dict[str, tuple] = {}
    for index, commit in enumerate(history):
        for path in commit.files:
            last_touched[path] = (commit.timestamp, index)
    candidates = [(touched, path) for path, touched in last_touched.items() if path in tracked]
    if len(candidates) < 2:
        return None
    (when, _), path = min(candidates)
    return Haunting("forgotten", "The most forgotten file", path, when, {"path": path})


def _graveyard(repo: Repo, history) -> Optional[Haunting]:
    deletions = [c for c in history if not c.is_merge and c.lines_deleted > 0]
    if not deletions:
        return None
    biggest = max(deletions, key=lambda c: c.lines_deleted)
    if biggest.lines_deleted < 20:
        return None
    subject = commit_subject(biggest.message)[:60]
    return Haunting(
        "graveyard",
        "The graveyard",
        f'{biggest.lines_deleted:,} lines buried in "{subject}"',
        biggest.timestamp,
        {"lines": biggest.lines_deleted, "subject": subject},
    )


def _witching_hour(repo: Repo, history) -> Optional[Haunting]:
    late = [c for c in history if 0 <= c.timestamp.hour < 4]
    if not late:
        return None
    latest = max(late, key=lambda c: (c.timestamp.hour, c.timestamp.minute))
    return Haunting(
        "witching",
        "Commits at the witching hour",
        f"{len(late)} between midnight and 4am, the latest at {latest.timestamp:%H:%M}",
        latest.timestamp,
        {"count": len(late), "latest": f"{latest.timestamp:%H:%M}"},
    )


def _first_spirit(repo: Repo, history) -> Optional[Haunting]:
    for commit in history:
        agent = detect_agent(commit.message, commit.author_name, commit.author_email)
        if agent:
            subject = commit_subject(commit.message)[:60]
            return Haunting(
                "spirit",
                "The first spirit",
                f'{agent} wrote "{subject}"',
                commit.timestamp,
                {"agent": agent, "subject": subject},
            )
    return None
