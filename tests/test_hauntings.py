import subprocess
from pathlib import Path

from gitgotchi.seance.hauntings import find_hauntings


def commit(repo, files, message):
    root = Path(repo.working_tree_dir)
    for name, content in files.items():
        path = root / name
        if content is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


def test_finds_todo_graveyard_and_spirit(repo):
    commit(repo, {"old.py": "x = 1\n", "big.py": "line\n" * 50}, "feat: start")
    commit(repo, {"app.py": "def f():\n    pass  # TODO: haunt this\n"}, "feat: app")
    commit(repo, {"big.py": None}, "chore: bury the big file")
    commit(
        repo,
        {"app.py": "def f():\n    pass  # TODO: haunt this\n\ndef g():\n    pass\n"},
        "feat: g\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
    )

    found = find_hauntings(repo).by_kind()

    assert found["todo"].facts["path"] == "app.py"
    assert found["todo"].facts["note"] == "TODO: haunt this"
    assert found["graveyard"].facts["lines"] == 50
    assert found["spirit"].facts["agent"] == "Claude"
    assert found["forgotten"].facts["path"] == "old.py"


def test_empty_repo_has_no_hauntings(repo):
    assert not find_hauntings(repo)


def test_non_ascii_paths_and_renames(repo):
    from gitgotchi.history import read_history

    commit(repo, {"old_name.py": "x = 1\n" * 3}, "feat: start")
    commit(repo, {"café.py": "def f():\n    pass  # TODO: café later\n"}, "feat: café")
    root = Path(repo.working_tree_dir)
    subprocess.run(["git", "mv", "old_name.py", "new_name.py"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "refactor: rename"], cwd=root, check=True)

    files = [f for c in read_history(repo) for f in c.files]
    assert "café.py" in files
    assert not any("=>" in f for f in files)

    found = find_hauntings(repo).by_kind()
    assert found["todo"].facts["path"] == "café.py"
