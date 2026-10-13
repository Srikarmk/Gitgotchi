"""Locate the git repository and GitGotchi's state inside it."""
from pathlib import Path
from typing import Optional

from git import InvalidGitRepositoryError, NoSuchPathError, Repo

STATE_DIR = ".gitgotchi"


class NotInRepositoryError(RuntimeError):
    """Raised when GitGotchi is used outside a git working tree."""

    def __init__(self) -> None:
        super().__init__("No git repository found here. Run `git init` first.")


def find_repo(path: str = ".") -> Optional[Repo]:
    """Find the git repository containing `path`.

    Returns:
        Repo instance, or None if not inside a non-bare git repository
    """
    try:
        repo = Repo(path, search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError):
        return None
    if repo.working_tree_dir is None:
        return None
    return repo


def require_repo(path: str = ".") -> Repo:
    """Like find_repo, but raise NotInRepositoryError instead of returning None."""
    repo = find_repo(path)
    if repo is None:
        raise NotInRepositoryError()
    return repo


def state_db_path(repo: Repo) -> Path:
    """Path to the pet database, always at the root of the working tree."""
    return Path(repo.working_tree_dir) / STATE_DIR / "state.db"


def ignore_state_dir(repo: Repo) -> None:
    """Keep .gitgotchi/ out of `git status` using the repo-local exclude file.

    .git/info/exclude is never committed, so this doesn't touch the user's
    .gitignore.
    """
    exclude = Path(repo.common_dir) / "info" / "exclude"
    entry = f"/{STATE_DIR}/"
    existing = exclude.read_text() if exclude.exists() else ""
    if entry in existing.splitlines():
        return

    exclude.parent.mkdir(parents=True, exist_ok=True)
    with open(exclude, "a") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write(entry + "\n")
