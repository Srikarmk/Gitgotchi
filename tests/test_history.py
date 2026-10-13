import subprocess
from pathlib import Path

from sqlalchemy import create_engine, text

from gitgotchi.db.state_manager import StateManager
from gitgotchi.history import read_history
from gitgotchi.pet.states import PetForm

CLAUDE = "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"


def make_commits(repo, messages):
    root = Path(repo.working_tree_dir)
    for i, message in enumerate(messages):
        (root / f"file{i}.py").write_text("a\nb\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


def test_read_history_is_oldest_first_with_line_counts(repo):
    make_commits(repo, ["feat: first", "feat: second"])
    history = read_history(repo)
    assert [c.message for c in history] == ["feat: first", "feat: second"]
    assert history[0].lines_added == 2
    assert history[0].files == ["file0.py"]


def test_read_history_on_empty_repo(repo):
    assert read_history(repo) == []


def test_replay_counts_agents_and_evolves(repo):
    make_commits(repo, [f"feat: add spooky feature number {i}" + CLAUDE for i in range(6)] + ["feat: mine"])
    manager = StateManager()

    replay = manager.replay_history(read_history(repo))

    assert replay.count == 7
    assert replay.agents["Claude"] == 6
    assert replay.stats.current_form == PetForm.POLTERGEIST
    assert manager.get_pet_state().ai_commits == 6
    assert manager.replay_history(read_history(repo)).count == 0


def test_reset_keeps_name(repo):
    make_commits(repo, ["feat: one", "feat: two", "feat: three"])
    manager = StateManager()
    stats = manager.get_pet_state()
    stats.pet_name = "Jack"
    manager.save_pet_state(stats)
    manager.replay_history(read_history(repo))

    manager.reset()

    stats = manager.get_pet_state()
    assert stats.pet_name == "Jack"
    assert stats.total_commits == 0
    assert not manager.has_commit(repo.head.commit.hexsha)


def test_upgrades_database_from_0_2(repo):
    db = Path(repo.working_tree_dir) / ".gitgotchi" / "state.db"
    db.parent.mkdir()
    engine = create_engine(f"sqlite:///{db}")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE pet_state (id INTEGER PRIMARY KEY, pet_name VARCHAR(100), total_commits INTEGER,"
            " lines_added INTEGER, lines_deleted INTEGER, merge_conflicts INTEGER, reverts INTEGER,"
            " quality_score FLOAT, evolution_points INTEGER, friend_level FLOAT, last_fed DATETIME,"
            " current_mood VARCHAR(20), current_form VARCHAR(20), created_at DATETIME, updated_at DATETIME)"
        ))
        conn.execute(text(
            "INSERT INTO pet_state VALUES (1, 'Old', 9, 10, 2, 0, 0, 61.0, 0, 3.0,"
            " '2026-01-01 00:00:00', 'content', 'ghost', '2025-12-02 00:00:00', '2026-01-01 00:00:00')"
        ))
        conn.execute(text(
            "CREATE TABLE commit_history (id INTEGER PRIMARY KEY, commit_hash VARCHAR(40), author VARCHAR(255),"
            " message TEXT, timestamp DATETIME, lines_added INTEGER, lines_deleted INTEGER, files_changed INTEGER,"
            " is_merge BOOLEAN, is_revert BOOLEAN, quality_impact FLOAT, processed_at DATETIME)"
        ))

    stats = StateManager().get_pet_state()

    assert stats.pet_name == "Old"
    assert stats.total_commits == 9
    assert stats.ai_commits == 0
