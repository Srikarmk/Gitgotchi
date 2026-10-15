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


def test_state_lives_in_git_dir_and_never_shows_in_status(repo):
    StateManager().save_pet_state(_named("Boo"))

    assert (Path(repo.git_dir) / "gitgotchi" / "state.db").exists()
    assert repo.untracked_files == []


def test_moves_legacy_state_into_git_dir(repo):
    root = Path(repo.working_tree_dir)
    legacy = root / ".gitgotchi" / "state.db"
    legacy.parent.mkdir()
    old = StateManager(str(legacy))
    old.save_pet_state(_named("Old"))
    old.close()

    assert StateManager().get_pet_state().pet_name == "Old"
    assert not legacy.exists()
    assert not legacy.parent.exists()


def test_worktrees_share_one_pet(repo, tmp_path, monkeypatch):
    import subprocess

    root = Path(repo.working_tree_dir)
    (root / "a.txt").write_text("a")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "feat: a"], cwd=root, check=True)
    StateManager().save_pet_state(_named("Shared"))

    worktree = tmp_path / "wt"
    subprocess.run(["git", "worktree", "add", "-q", str(worktree), "-b", "side"], cwd=root, check=True)
    monkeypatch.chdir(worktree)

    assert StateManager().get_pet_state().pet_name == "Shared"


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


def test_concurrent_writers_do_not_lose_updates(repo):
    import threading

    from sqlalchemy.orm import Session

    from gitgotchi.db.models import CommitHistory
    from gitgotchi.history import HistoryCommit

    history = [
        HistoryCommit(f"{i:040x}", "Dev", "dev@example.com", datetime.now(), 1, f"feat: old {i}", 1, 0, ["a.py"])
        for i in range(200)
    ]
    path = StateManager().db_path
    errors = []

    def replay():
        try:
            StateManager(path).replay_history(history)
        except Exception as e:
            errors.append(e)

    def hook():
        try:
            manager = StateManager(path)
            for i in range(20):
                _commit(manager, f"live{i:036x}", f"feat: live {i}")
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=replay), threading.Thread(target=hook)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors
    manager = StateManager(path)
    with Session(manager.engine) as session:
        assert session.query(CommitHistory).count() == 220
    assert manager.get_pet_state().total_commits == 220


def test_adopting_old_history_keeps_the_pet_awake(repo):
    from datetime import timedelta

    from gitgotchi.history import HistoryCommit
    from gitgotchi.pet.states import PetMood

    manager = StateManager()
    _commit(manager, "today", "feat: fed just now")
    old = datetime.now() - timedelta(days=900)
    manager.replay_history([HistoryCommit("a" * 40, "Dev", "d@x.com", old, 1, "feat: ancient", 1, 0, [])])

    assert manager.get_pet_state().current_mood != PetMood.SLEEPING


def test_keeps_using_legacy_state_if_it_cannot_be_moved(repo, monkeypatch):
    import shutil

    root = Path(repo.working_tree_dir)
    legacy = root / ".gitgotchi" / "state.db"
    legacy.parent.mkdir()
    old = StateManager(str(legacy))
    old.save_pet_state(_named("Busy"))
    old.close()

    def locked(*args, **kwargs):
        raise PermissionError("file is in use")

    monkeypatch.setattr(shutil, "move", locked)
    assert StateManager().get_pet_state().pet_name == "Busy"
    assert legacy.exists()
