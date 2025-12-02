"""Hook installation."""
import os
import sys
from pathlib import Path
from typing import Optional

from git import InvalidGitRepositoryError, Repo
from rich.console import Console

console = Console()


def find_git_root() -> Optional[Path]:
    """Find git repository root.

    Returns:
        Path to git root, or None if not in a git repo
    """
    try:
        repo = Repo(".", search_parent_directories=True)
        return Path(repo.git_dir).parent
    except InvalidGitRepositoryError:
        return None


def install_hooks() -> bool:
    """Install git hooks for GitGotchi.

    Returns:
        True if successful, False otherwise
    """
    git_root = find_git_root()

    if not git_root:
        console.print(
            "[red]👻 No git repository found! Initialize git first.[/red]"
        )
        return False

    hooks_dir = git_root / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    post_commit_path = hooks_dir / "post-commit"

    # GitGotchi hook content
    python_path = sys.executable
    gitgotchi_hook = f"""#!/bin/sh
# GitGotchi post-commit hook
{python_path} -m src.hooks.post_commit
"""

    # Check if hook already exists
    if post_commit_path.exists():
        existing_content = post_commit_path.read_text()

        if "GitGotchi" in existing_content:
            console.print("[yellow]👻 GitGotchi hooks already installed![/yellow]")
            return True

        # Append to existing hook
        console.print(
            "[yellow]⚠️  Existing post-commit hook found. Appending GitGotchi...[/yellow]"
        )
        with open(post_commit_path, "a") as f:
            f.write("\n" + gitgotchi_hook)
    else:
        # Create new hook
        post_commit_path.write_text(gitgotchi_hook)

    # Make executable
    post_commit_path.chmod(0o755)

    console.print("[green]✨ GitGotchi hooks installed successfully![/green]")
    console.print(f"[dim]Hook location: {post_commit_path}[/dim]")

    return True


def uninstall_hooks() -> bool:
    """Uninstall GitGotchi git hooks.

    Returns:
        True if successful, False otherwise
    """
    git_root = find_git_root()

    if not git_root:
        console.print("[red]👻 No git repository found![/red]")
        return False

    post_commit_path = git_root / ".git" / "hooks" / "post-commit"

    if not post_commit_path.exists():
        console.print("[yellow]👻 No hooks found to uninstall.[/yellow]")
        return True

    existing_content = post_commit_path.read_text()

    if "GitGotchi" not in existing_content:
        console.print("[yellow]👻 GitGotchi hooks not found.[/yellow]")
        return True

    # Remove GitGotchi section
    lines = existing_content.split("\n")
    filtered_lines = []
    skip_next = False

    for line in lines:
        if "GitGotchi" in line:
            skip_next = True
            continue
        if skip_next and line.strip().startswith("python"):
            skip_next = False
            continue
        filtered_lines.append(line)

    new_content = "\n".join(filtered_lines).strip()

    if new_content and new_content != "#!/bin/sh":
        # Other hooks remain, update file
        post_commit_path.write_text(new_content)
        console.print("[green]✨ GitGotchi hooks removed.[/green]")
    else:
        # No other hooks, delete file
        post_commit_path.unlink()
        console.print("[green]✨ GitGotchi hooks removed (file deleted).[/green]")

    return True
