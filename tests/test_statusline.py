import io
import subprocess
from pathlib import Path

from gitgotchi.db.state_manager import StateManager
from gitgotchi.statusline import find_state_db, load_stats, main, render_line


def make_pet(repo, name="Boo", ai=0):
    manager = StateManager()
    stats = manager.get_pet_state()
    stats.pet_name = name
    stats.total_commits = 8
    stats.ai_commits = ai
    manager.save_pet_state(stats)
    manager.close()


def test_finds_the_pet_from_a_subdirectory(repo):
    make_pet(repo)
    sub = Path(repo.working_tree_dir) / "a" / "b"
    sub.mkdir(parents=True)
    assert find_state_db(sub) == Path(repo.git_dir) / "gitgotchi" / "state.db"


def test_finds_the_pet_from_a_worktree(repo, tmp_path):
    root = Path(repo.working_tree_dir)
    (root / "a.txt").write_text("a")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "feat: a"], cwd=root, check=True)
    make_pet(repo, "Shared")
    worktree = tmp_path / "wt"
    subprocess.run(["git", "worktree", "add", "-q", str(worktree), "-b", "side"], cwd=root, check=True)

    assert load_stats(find_state_db(worktree)).pet_name == "Shared"


def test_line_shows_name_form_possession_and_mood(repo):
    make_pet(repo, ai=5)
    line = render_line(load_stats(find_state_db(Path.cwd())), color=False)
    assert line.startswith("🎃 Boo the Pumpkin")
    assert "62% possessed" in line
    assert "content" in line or "cheerful" in line


def test_reads_the_directory_from_claude_codes_json(repo, tmp_path, monkeypatch, capsys):
    make_pet(repo, "FromJson")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO('{"workspace": {"current_dir": "%s"}}' % repo.working_tree_dir))

    main(["--plain"])

    assert "FromJson" in capsys.readouterr().out


def test_prints_nothing_outside_a_haunted_repo(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert main([]) == 0
    assert capsys.readouterr().out == ""
