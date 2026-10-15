import os
import stat
import subprocess
from pathlib import Path


from gitgotchi.db.state_manager import StateManager
from gitgotchi.hooks.installer import (
    HOOK_START,
    hooks_dir,
    install_hooks,
    uninstall_hooks,
)

LEGACY_HOOK = (
    "#!/bin/sh\n"
    "# GitGotchi post-commit hook\n"
    '"/old/venv/bin/python" -m src.hooks.post_commit\n'
)


def hook_path(repo) -> Path:
    return hooks_dir(repo) / "post-commit"


def test_install_creates_executable_hook(repo):
    assert install_hooks()

    content = hook_path(repo).read_text()
    assert content.startswith("#!/bin/sh\n")
    assert HOOK_START in content
    assert "-m gitgotchi.hooks.post_commit" in content
    if os.name != "nt":
        assert hook_path(repo).stat().st_mode & stat.S_IXUSR


def test_install_is_idempotent(repo):
    install_hooks()
    first = hook_path(repo).read_text()
    install_hooks()
    assert hook_path(repo).read_text() == first


def test_install_migrates_legacy_hook(repo):
    hook_path(repo).parent.mkdir(parents=True, exist_ok=True)
    hook_path(repo).write_text(LEGACY_HOOK)

    install_hooks()

    content = hook_path(repo).read_text()
    assert "src.hooks.post_commit" not in content
    assert content.count(HOOK_START) == 1


def test_uninstall_removes_legacy_hook_completely(repo):
    hook_path(repo).parent.mkdir(parents=True, exist_ok=True)
    hook_path(repo).write_text(LEGACY_HOOK)

    uninstall_hooks()

    assert not hook_path(repo).exists()


def test_uninstall_keeps_other_hooks(repo):
    hook_path(repo).parent.mkdir(parents=True, exist_ok=True)
    hook_path(repo).write_text("#!/bin/sh\necho other\n")

    install_hooks()
    uninstall_hooks()

    assert hook_path(repo).read_text() == "#!/bin/sh\necho other\n"


def test_respects_core_hooks_path(repo):
    with repo.config_writer() as cw:
        cw.set_value("core", "hooksPath", ".githooks")

    install_hooks()

    assert (Path(repo.working_tree_dir) / ".githooks" / "post-commit").exists()


def test_commit_feeds_pet_end_to_end(repo):
    install_hooks()
    root = Path(repo.working_tree_dir)
    (root / "src").mkdir()
    (root / "src" / "__init__.py").write_text("")
    (root / "app.py").write_text("print('boo')\n")

    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "feat: summon the first spirit"],
        cwd=root,
        check=True,
        capture_output=True,
    )

    stats = StateManager().get_pet_state()
    assert stats.total_commits == 1
    assert stats.lines_added == 1
    assert repo.is_dirty(untracked_files=True) is False


def test_amending_does_not_count_twice(repo):
    install_hooks()
    root = Path(repo.working_tree_dir)
    (root / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "feat: original"], cwd=root, check=True, capture_output=True)
    for message in ("feat: amended once", "feat: amended twice"):
        subprocess.run(["git", "commit", "-q", "--amend", "-m", message], cwd=root, check=True, capture_output=True)

    manager = StateManager()
    assert manager.get_pet_state().total_commits == 1
    assert manager.has_commit(repo.head.commit.hexsha)
    assert manager.get_recent_commits() == ["feat: amended twice"]


def test_hook_quotes_unusual_python_paths(repo, monkeypatch):
    monkeypatch.setattr("sys.executable", "/tmp/we$ird `path`/bin/python")
    install_hooks()
    content = hook_path(repo).read_text()
    assert "GITGOTCHI_PYTHON='/tmp/we$ird `path`/bin/python'" in content


def test_block_goes_right_after_the_shebang(repo):
    hook_path(repo).parent.mkdir(parents=True, exist_ok=True)
    hook_path(repo).write_text("#!/bin/bash\necho before\nexit 0\n")

    install_hooks()

    content = hook_path(repo).read_text()
    assert content.startswith("#!/bin/bash\n" + HOOK_START)
    assert content.index(HOOK_START) < content.index("exit 0")
    uninstall_hooks()
    assert hook_path(repo).read_text() == "#!/bin/bash\necho before\nexit 0\n"


def test_refuses_non_shell_hooks(repo):
    hook_path(repo).parent.mkdir(parents=True, exist_ok=True)
    hook_path(repo).write_text("#!/usr/bin/env python3\nprint('hi')\n")

    assert install_hooks() is False
    assert HOOK_START not in hook_path(repo).read_text()


def test_markup_in_pet_name_keeps_hook_output_to_one_line(repo):
    manager = StateManager()
    stats = manager.get_pet_state()
    stats.pet_name = "[/] [bold]x"
    manager.save_pet_state(stats)
    install_hooks()
    root = Path(repo.working_tree_dir)
    (root / "a.py").write_text("x\n")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    result = subprocess.run(["git", "commit", "-q", "-m", "feat: a"], cwd=root, check=True, capture_output=True, text=True)

    output = (result.stdout + result.stderr).strip().splitlines()
    assert len(output) == 1
    assert "[/] [bold]x" in output[0]
