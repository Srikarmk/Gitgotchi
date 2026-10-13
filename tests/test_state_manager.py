from datetime import datetime
from pathlib import Path

import pytest

from gitgotchi.db.state_manager import StateManager
from gitgotchi.paths import NotInRepositoryError


def test_state_lives_at_repo_root_from_subdirectory(repo, monkeypatch):
    root = Path(repo.working_tree_dir)
    sub = root / "a" / "b"
    sub.mkdir(parents=True)

    StateManager().save_pet_state(_named("Boo"))
    monkeypatch.chdir(sub)

    assert StateManager().get_pet_state().pet_name == "Boo"
    assert not (sub / ".gitgotchi").exists()


def test_state_dir_is_excluded_from_git(repo):
    StateManager()
    StateManager()

    exclude = Path(repo.git_dir) / "info" / "exclude"
    assert exclude.read_text().splitlines().count("/.gitgotchi/") == 1
    assert repo.untracked_files == []


def test_outside_repo_raises(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(NotInRepositoryError):
        StateManager()


def test_process_commit_event_updates_stats(repo):
    manager = StateManager()
    stats = _commit(manager, "abc", "feat: add a haunted lantern", files=["tests/test_a.py"])

    assert stats.total_commits == 1
    assert stats.quality_score > 50
    assert manager.has_commit("abc")
    assert manager.get_recent_commits() == ["feat: add a haunted lantern"]


def test_merge_commits_do_not_move_quality(repo):
    manager = StateManager()
    stats = _commit(manager, "m1", "Merge branch 'x'", is_merge=True)
    assert stats.quality_score == 50
    assert stats.merge_conflicts == 1


def _named(name):
    from gitgotchi.pet.states import PetStats

    stats = PetStats()
    stats.pet_name = name
    return stats


def _commit(manager, sha, message, files=(), is_merge=False):
    return manager.process_commit_event(
        commit_hash=sha,
        author="Test User",
        message=message,
        timestamp=datetime.now(),
        lines_added=10,
        lines_deleted=2,
        files_changed=len(files),
        is_merge=is_merge,
        files=files,
    )
