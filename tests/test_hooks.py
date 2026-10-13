import os
import stat
import subprocess
from pathlib import Path

import pytest

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
