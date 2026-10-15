"""`gitgotchi-statusline`: one line about your pet, for status bars and prompts.

Status lines run constantly (Claude Code refreshes its own several times a
second), so this deliberately avoids the heavy imports the main CLI needs:
no numpy, Rich, SQLAlchemy or GitPython, just the standard library.
"""
import argparse
import json
import sqlite3
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from gitgotchi.pet import theme
from gitgotchi.pet.states import PetForm, PetMood, PetStats

RESET = "\x1b[0m"


def find_state_db(start: Path) -> Optional[Path]:
    """The pet database for the repo containing `start`, if there is one."""
    for folder in [start, *start.parents]:
        dot_git = folder / ".git"
        if dot_git.is_dir():
            git_dir = dot_git
        elif dot_git.is_file():
            # A linked worktree: .git is a file pointing at the real git dir
            pointer = dot_git.read_text().strip()
            if not pointer.startswith("gitdir:"):
                return None
            git_dir = (folder / pointer[len("gitdir:"):].strip()).resolve()
        else:
            continue

        common = git_dir
        commondir = git_dir / "commondir"
        if commondir.is_file():
            common = (git_dir / commondir.read_text().strip()).resolve()

        for candidate in (common / "gitgotchi" / "state.db", folder / ".gitgotchi" / "state.db"):
            if candidate.is_file():
                return candidate
        return None
    return None


def load_stats(db: Path) -> Optional[PetStats]:
    try:
        conn = sqlite3.connect(_sqlite_uri(db), uri=True, timeout=1)
    except sqlite3.Error:
        return None
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM pet_state LIMIT 1").fetchone()
    except sqlite3.Error:
        return None
    finally:
        conn.close()
    if row is None:
        return None

    columns = row.keys()
    stats = PetStats()
    stats.pet_name = row["pet_name"]
    stats.total_commits = row["total_commits"] or 0
    stats.ai_commits = (row["ai_commits"] if "ai_commits" in columns else 0) or 0
    stats.quality_score = row["quality_score"] or 50.0
    stats.current_form = PetForm(row["current_form"])
    stats.last_fed = _parse_time(row["last_fed"]) or datetime.now()
    if "last_visit" in columns:
        stats.last_visit = _parse_time(row["last_visit"])
    stats.update_mood()
    return stats


def render_line(stats: PetStats, color: bool = True) -> str:
    info = theme.form_info(stats.current_form)
    mood = theme.MOODS[stats.current_mood][0]

    def paint(text: str, hex_color: str, bold: bool = False) -> str:
        if not color:
            return text
        r, g, b = (int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        return f"\x1b[{'1;' if bold else ''}38;2;{r};{g};{b}m{text}{RESET}"

    sep = paint(" · ", theme.DIM)
    name = stats.pet_name if stats.pet_name == info.title else f"{stats.pet_name} the {info.title}"
    parts = [f"{info.icon} " + paint(name, info.color, bold=True)]
    if stats.ai_commits:
        parts.append(paint(f"{stats.possession:.0%} possessed", theme.CYAN))
    mood_color = theme.ORANGE if stats.current_mood in (PetMood.HUNGRY, PetMood.TIRED, PetMood.SLEEPING) else theme.DIM
    parts.append(paint(mood, mood_color))
    return sep.join(parts)


SETUP = """\
Claude Code: add this to ~/.claude/settings.json
  "statusLine": {"type": "command", "command": "gitgotchi-statusline"}

tmux: add this to ~/.tmux.conf
  set -g status-right '#(cd #{pane_current_path} && gitgotchi-statusline --plain)'

Starship: add this to ~/.config/starship.toml
  [custom.gitgotchi]
  command = "gitgotchi-statusline --plain"
  when = "git rev-parse --git-dir"
  format = "$output "
"""


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gitgotchi-statusline",
        description="Print one line about the GitGotchi in the current repo.",
    )
    parser.add_argument("--plain", action="store_true", help="no colors (for tmux or Starship)")
    parser.add_argument("--dir", type=Path, help="repo to look in (default: current directory)")
    parser.add_argument("--setup", action="store_true", help="show how to add it to Claude Code, tmux and Starship")
    args = parser.parse_args(argv)

    if args.setup:
        print(SETUP, end="")
        return 0

    folder = args.dir or _dir_from_stdin() or Path.cwd()
    db = find_state_db(Path(folder).expanduser())
    stats = load_stats(db) if db else None
    # Outside a haunted repo, print nothing so the status bar stays clean
    if stats:
        _write(render_line(stats, color=not args.plain))
    return 0


def _dir_from_stdin() -> Optional[Path]:
    """Claude Code passes session details, including the working directory, as JSON."""
    if sys.stdin is None or sys.stdin.isatty():
        return None
    result = {}

    def read():
        try:
            result["text"] = sys.stdin.read()
        except (OSError, ValueError):
            pass

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    reader.join(0.25)  # never hang a status bar on an open, silent pipe
    try:
        data = json.loads(result.get("text") or "{}")
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    workspace = data.get("workspace") if isinstance(data.get("workspace"), dict) else {}
    folder = workspace.get("current_dir") or data.get("cwd")
    return Path(folder) if isinstance(folder, str) and folder else None


def _write(line: str) -> None:
    try:
        sys.stdout.write(line + "\n")
    except UnicodeEncodeError:
        sys.stdout.buffer.write((line + "\n").encode("utf-8"))


def _sqlite_uri(path: Path) -> str:
    """Read-only SQLite URI, built by hand: Path.as_uri() imports urllib.request,
    which costs more than everything else this command does."""
    posix = path.resolve().as_posix()
    if not posix.startswith("/"):
        posix = "/" + posix  # Windows drive paths: file:///C:/...
    return "file://" + quote(posix, safe="/:") + "?mode=ro"


def _parse_time(value) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


if __name__ == "__main__":
    sys.exit(main())
