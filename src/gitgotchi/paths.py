"""Locate the git repository and GitGotchi's state inside it."""
import shutil
from pathlib import Path
from typing import Optional

from git import InvalidGitRepositoryError, NoSuchPathError, Repo

LEGACY_STATE_DIR = ".gitgotchi"


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
    """Path to the pet database.

    It lives in the shared git directory, so every worktree of a repo feeds
    the same pet and the database can never be committed. Pets created by
    0.3.0 and earlier (in <worktree>/.gitgotchi/) are moved there.
    """
    path = Path(repo.common_dir) / "gitgotchi" / "state.db"
    legacy = Path(repo.working_tree_dir) / LEGACY_STATE_DIR / "state.db"
    if legacy.exists() and not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(legacy), str(path))
        try:
            legacy.parent.rmdir()
        except OSError:
            pass  # something else is in there; leave it alone
    return path
