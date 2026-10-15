"""Read a repository's commit history in a single git call."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from git import GitCommandError, Repo

RECORD = "\x1e"
FIELD = "\x1f"
END_OF_BODY = "\x1d"
FORMAT = f"{RECORD}%H{FIELD}%an{FIELD}%ae{FIELD}%ct{FIELD}%aI{FIELD}%P{FIELD}%B{END_OF_BODY}"

ESCAPES = {"n": b"\n", "t": b"\t", '"': b'"', "\\": b"\\", "a": b"\a", "b": b"\b", "f": b"\f", "r": b"\r", "v": b"\v"}


@dataclass
class HistoryCommit:
    hexsha: str
    author_name: str
    author_email: str
    timestamp: datetime
    parent_count: int
    message: str
    lines_added: int = 0
    lines_deleted: int = 0
    files: List[str] = field(default_factory=list)
    # When the author wrote it, in the author's own timezone
    authored: Optional[datetime] = None

    @property
    def is_merge(self) -> bool:
        return self.parent_count > 1

    @property
    def is_revert(self) -> bool:
        return self.message.lower().startswith("revert")


def unquote_path(path: str) -> str:
    """Undo git's C-style quoting of unusual paths ("caf\\303\\251.py" -> café.py)."""
    if len(path) < 2 or path[0] != '"' or path[-1] != '"':
        return path
    body, out, i = path[1:-1], bytearray(), 0
    while i < len(body):
        char = body[i]
        if char == "\\" and i + 1 < len(body):
            following = body[i + 1]
            if following in "01234567":
                out.append(int(body[i + 1 : i + 4], 8))
                i += 4
                continue
            out += ESCAPES.get(following, following.encode())
            i += 2
        else:
            out += char.encode()
            i += 1
    return out.decode("utf-8", "replace")


def read_history(repo: Repo, limit: Optional[int] = None, rev: str = "HEAD") -> List[HistoryCommit]:
    """Commits reachable from `rev`, oldest first, with line counts.

    Args:
        limit: Only the most recent `limit` commits
    """
    # --no-renames keeps paths real (no "dir/{old => new}") and matches what
    # GitPython's commit.stats reports for the hook
    args = [rev, f"--format={FORMAT}", "--numstat", "--no-renames", "--no-color", "--reverse"]
    if limit:
        args.append(f"--max-count={limit}")
    try:
        output = repo.git.log(*args, strip_newline_in_stdout=False)
    except GitCommandError:  # no commits yet
        return []

    commits = []
    for record in output.split(RECORD)[1:]:
        header, _, numstat = record.partition(END_OF_BODY)
        sha, name, email, ctime, authored, parents, message = header.split(FIELD, 6)
        commit = HistoryCommit(
            hexsha=sha,
            author_name=name,
            author_email=email,
            timestamp=datetime.fromtimestamp(int(ctime)),
            parent_count=len(parents.split()),
            message=message.strip(),
            authored=_parse_iso(authored),
        )
        for line in numstat.strip().splitlines():
            added, deleted, path = (line.split("\t", 2) + ["", "", ""])[:3]
            if not path:
                continue
            commit.files.append(unquote_path(path))
            # Binary files show "-" instead of a count
            commit.lines_added += int(added) if added.isdigit() else 0
            commit.lines_deleted += int(deleted) if deleted.isdigit() else 0
        commits.append(commit)
    return commits


def _parse_iso(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
