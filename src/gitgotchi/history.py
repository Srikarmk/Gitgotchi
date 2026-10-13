"""Read a repository's commit history in a single git call."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from git import GitCommandError, Repo

RECORD = "\x1e"
FIELD = "\x1f"
END_OF_BODY = "\x1d"
FORMAT = f"{RECORD}%H{FIELD}%an{FIELD}%ae{FIELD}%ct{FIELD}%P{FIELD}%B{END_OF_BODY}"


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

    @property
    def is_merge(self) -> bool:
        return self.parent_count > 1

    @property
    def is_revert(self) -> bool:
        return self.message.lower().startswith("revert")


def read_history(repo: Repo, limit: Optional[int] = None, rev: str = "HEAD") -> List[HistoryCommit]:
    """Commits reachable from `rev`, oldest first, with line counts.

    Args:
        limit: Only the most recent `limit` commits
    """
    args = [rev, f"--format={FORMAT}", "--numstat", "--no-color", "--reverse"]
    if limit:
        args.append(f"--max-count={limit}")
    try:
        output = repo.git.log(*args, strip_newline_in_stdout=False)
    except GitCommandError:  # no commits yet
        return []

    commits = []
    for record in output.split(RECORD)[1:]:
        header, _, numstat = record.partition(END_OF_BODY)
        sha, name, email, ctime, parents, message = header.split(FIELD, 5)
        commit = HistoryCommit(
            hexsha=sha,
            author_name=name,
            author_email=email,
            timestamp=datetime.fromtimestamp(int(ctime)),
            parent_count=len(parents.split()),
            message=message.strip(),
        )
        for line in numstat.strip().splitlines():
            added, deleted, path = (line.split("\t", 2) + ["", "", ""])[:3]
            if not path:
                continue
            commit.files.append(path)
            # Binary files show "-" instead of a count
            commit.lines_added += int(added) if added.isdigit() else 0
            commit.lines_deleted += int(deleted) if deleted.isdigit() else 0
        commits.append(commit)
    return commits
