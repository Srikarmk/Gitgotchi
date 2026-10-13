"""Hook installation."""
import sys
from pathlib import Path

from git import Repo
from rich.console import Console

from gitgotchi.paths import find_repo, ignore_state_dir

console = Console()

HOOK_START = "# >>> gitgotchi >>>"
HOOK_END = "# <<< gitgotchi <<<"

# Written by 0.1.x: a marker line followed by `"<python>" -m src.hooks.post_commit`
LEGACY_MARKER = "# GitGotchi post-commit hook"


def hooks_dir(repo: Repo) -> Path:
    """Directory git actually runs hooks from.

    Respects core.hooksPath and linked worktrees (where .git is a file).
    """
    path = Path(repo.git.rev_parse("--git-path", "hooks"))
    if not path.is_absolute():
        path = Path(repo.working_tree_dir) / path
    return path


def hook_block() -> str:
    """Shell snippet that feeds the pet from this Python environment."""
    python_path = sys.executable.replace("\\", "/")
    return (
        f"{HOOK_START}\n"
        f'GITGOTCHI_PYTHON="{python_path}"\n'
        'if [ -x "$GITGOTCHI_PYTHON" ]; then\n'
        '    "$GITGOTCHI_PYTHON" -m gitgotchi.hooks.post_commit\n'
        "fi\n"
        f"{HOOK_END}\n"
    )


def has_gitgotchi(content: str) -> bool:
    return HOOK_START in content or LEGACY_MARKER in content


def strip_gitgotchi(content: str) -> str:
    """Remove GitGotchi's section from a hook, leaving everything else intact."""
    kept = []
    in_block = False
    skip_legacy_command = False

    for line in content.splitlines():
        if line.strip() == HOOK_START:
            in_block = True
            continue
        if in_block:
            if line.strip() == HOOK_END:
                in_block = False
            continue
        if line.strip() == LEGACY_MARKER:
            skip_legacy_command = True
            continue
        if skip_legacy_command:
            skip_legacy_command = False
            if "hooks.post_commit" in line:
                continue
        kept.append(line)

    return "\n".join(kept).rstrip() + "\n" if kept else ""


def is_empty_hook(content: str) -> bool:
    return content.strip() in ("", "#!/bin/sh")


def install_hooks() -> bool:
    """Install git hooks for GitGotchi.

    Returns:
        True if successful, False otherwise
    """
    repo = find_repo()

    if repo is None:
        console.print(
            "[red]👻 No git repository found! Initialize git first.[/red]"
        )
        return False

    directory = hooks_dir(repo)
    directory.mkdir(parents=True, exist_ok=True)
    post_commit_path = directory / "post-commit"

    existing = post_commit_path.read_text() if post_commit_path.exists() else ""
    already_installed = has_gitgotchi(existing)
    others = strip_gitgotchi(existing)

    if is_empty_hook(others):
        others = "#!/bin/sh\n"
    elif not already_installed:
        console.print(
            "[yellow]⚠️  Existing post-commit hook found. Appending GitGotchi...[/yellow]"
        )

    post_commit_path.write_text(others + "\n" + hook_block())
    post_commit_path.chmod(0o755)
    ignore_state_dir(repo)

    if already_installed:
        console.print("[green]✨ GitGotchi hooks updated![/green]")
    else:
        console.print("[green]✨ GitGotchi hooks installed successfully![/green]")
    console.print(f"[dim]Hook location: {post_commit_path}[/dim]")

    return True


def uninstall_hooks() -> bool:
    """Uninstall GitGotchi git hooks.

    Returns:
        True if successful, False otherwise
    """
    repo = find_repo()

    if repo is None:
        console.print("[red]👻 No git repository found![/red]")
        return False

    post_commit_path = hooks_dir(repo) / "post-commit"

    if not post_commit_path.exists():
        console.print("[yellow]👻 No hooks found to uninstall.[/yellow]")
        return True

    existing = post_commit_path.read_text()

    if not has_gitgotchi(existing):
        console.print("[yellow]👻 GitGotchi hooks not found.[/yellow]")
        return True

    remaining = strip_gitgotchi(existing)

    if is_empty_hook(remaining):
        post_commit_path.unlink()
        console.print("[green]✨ GitGotchi hooks removed (file deleted).[/green]")
    else:
        post_commit_path.write_text(remaining)
        console.print("[green]✨ GitGotchi hooks removed.[/green]")

    return True
