"""Dig spooky facts out of a repository's history for the séance."""
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from git import GitCommandError, Repo

from gitgotchi.history import HistoryCommit, read_history, unquote_path
from gitgotchi.pet.possession import detect_agent
from gitgotchi.pet.quality import commit_subject

TODO = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
MAX_FILES = 60
MAX_TODOS_PER_FILE = 40


def _split_grep_line(line: str) -> Tuple[str, str, str]:
    """Split `git grep -n` output into (path, line number, text).

    Unusual paths come back quoted ("caf\\303\\251.py":3:...), so the path can't
    just be split off at the first colon.
    """
    if line.startswith('"'):
        end = 1
        while end < len(line) and not (line[end] == '"' and line[end - 1] != "\\"):
            end += 1
        path, rest = unquote_path(line[: end + 1]), line[end + 2 :]
        number, _, text = rest.partition(":")
        return path, number, text
    path, number, text = (line.split(":", 2) + ["", ""])[:3]
    return path, number, text


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

    by_file: Dict[str, List[Tuple[str, str]]] = {}
    for line in output.splitlines():
        path, number, text = _split_grep_line(line)
        if number.isdigit() and TODO.search(text):
            by_file.setdefault(path, []).append((number, text))

    # One blame per file covering all its TODO lines, for up to MAX_FILES files
    oldest = None
    for path, todos in list(by_file.items())[:MAX_FILES]:
        ranges = [arg for number, _ in todos[:MAX_TODOS_PER_FILE] for arg in ("-L", f"{number},{number}")]
        try:
            blame = repo.git.blame("--line-porcelain", *ranges, "--", path)
        except GitCommandError:
            continue
        stamps = [int(s) for s in re.findall(r"^author-time (\d+)", blame, re.MULTILINE)]
        for (number, text), stamp in zip(todos, stamps):
            when = datetime.fromtimestamp(stamp)
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
    tracked = {unquote_path(p) for p in repo.git.ls_files().splitlines()}
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
    # The author's own clock: 2am for them, whatever timezone you're in
    late = [(c.authored or c.timestamp, c) for c in history]
    late = [(when, c) for when, c in late if 0 <= when.hour < 4]
    if not late:
        return None
    latest, _ = max(late, key=lambda pair: (pair[0].hour, pair[0].minute))
    return Haunting(
        "witching",
        "Commits at the witching hour",
        f"{len(late)} between midnight and 4am, the latest at {latest:%H:%M}",
        latest.replace(tzinfo=None),
        {"count": len(late), "latest": f"{latest:%H:%M}"},
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
