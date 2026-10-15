"""`gitgotchi doctor`: check every place setup can go wrong, with a fix for each."""
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from gitgotchi import __version__

OK, WARN, FAIL = "ok", "warn", "fail"


@dataclass
class Check:
    status: str
    name: str
    detail: str
    fix: str = ""


def run_checks(console) -> List[Check]:
    from gitgotchi.paths import find_repo

    checks = [
        Check(OK, "GitGotchi", f"{__version__} on Python {platform.python_version()} ({sys.executable})"),
        _git_check(),
    ]

    repo = find_repo()
    if repo is None:
        checks.append(Check(FAIL, "Repository", "not inside a git repository", "cd into a repo, or run `git init`"))
        checks.extend(_terminal_checks(console))
        checks.append(_api_key_check())
        return checks

    checks.append(Check(OK, "Repository", repo.working_tree_dir))
    checks.append(_pet_check())
    checks.extend(_hook_checks(repo))
    checks.append(_output_check(repo))
    checks.extend(_terminal_checks(console))
    checks.append(_api_key_check())
    return checks


def _git_check() -> Check:
    git = shutil.which("git")
    if not git:
        return Check(FAIL, "git", "not found on PATH", "install git from https://git-scm.com")
    try:
        version = subprocess.run([git, "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError) as e:
        return Check(FAIL, "git", str(e), "check that git runs from this terminal")
    return Check(OK, "git", version)


def _pet_check() -> Check:
    from gitgotchi.db.state_manager import StateManager

    try:
        manager = StateManager()
        stats = manager.get_pet_state()
        path = manager.db_path
        manager.close()
    except Exception as e:
        return Check(FAIL, "Pet", f"can't open the pet database: {e}", "check the permissions of .git/gitgotchi/")
    if ".gitgotchi" in Path(path).parts:
        return Check(WARN, "Pet", f"still in the old location {path}", "close any running `gitgotchi haunt`, then run any gitgotchi command to move it")
    return Check(OK, "Pet", f"{stats.pet_name}, {stats.total_commits} commits ({path})")


def _hook_checks(repo) -> List[Check]:
    from gitgotchi.hooks.installer import HOOK_START, LEGACY_MARKER, hooks_dir

    hook = hooks_dir(repo) / "post-commit"
    if not hook.exists():
        return [Check(WARN, "Hook", "not installed, so commits don't feed your pet", "run `gitgotchi install`")]

    content = hook.read_text(errors="replace")
    if HOOK_START not in content:
        if LEGACY_MARKER in content:
            return [Check(FAIL, "Hook", "left over from an older GitGotchi", "run `gitgotchi install` to update it")]
        return [Check(WARN, "Hook", f"{hook} exists but has no GitGotchi block", "run `gitgotchi install`")]

    checks = [Check(OK, "Hook", str(hook))]
    before = content.split(HOOK_START, 1)[0]
    if re.search(r"^\s*(exit|exec)\b", before, re.MULTILINE):
        checks.append(Check(FAIL, "Hook order", "an `exit` or `exec` runs before GitGotchi's block", "run `gitgotchi install` to move the block up"))

    if os.name != "nt" and not os.access(hook, os.X_OK):
        checks.append(Check(FAIL, "Hook permissions", "the hook isn't executable", f"chmod +x {hook}"))

    python = _hook_python(content)
    if python is None:
        checks.append(Check(WARN, "Hook Python", "couldn't read which Python the hook uses", "run `gitgotchi install`"))
    elif not Path(python).exists():
        checks.append(Check(FAIL, "Hook Python", f"{python} no longer exists", "run `gitgotchi install` from the environment GitGotchi is installed in"))
    else:
        probe = _probe(python)
        if probe is None:
            checks.append(Check(FAIL, "Hook Python", f"{python} can't import gitgotchi", "run `gitgotchi install` from the environment GitGotchi is installed in"))
        elif probe != __version__:
            checks.append(Check(WARN, "Hook Python", f"{python} has GitGotchi {probe}, this is {__version__}", "run `gitgotchi install` to point the hook here"))
        else:
            checks.append(Check(OK, "Hook Python", python))

    hooks_path = _git_config(repo, "core.hooksPath")
    if hooks_path:
        checks.append(Check(WARN, "core.hooksPath", f"hooks come from {hooks_path} (husky or a similar tool)", "if another tool rewrites that folder, re-run `gitgotchi install` after it does"))
    return checks


def _output_check(repo) -> Check:
    from gitgotchi.hooks.post_commit import configured_output

    style = configured_output(repo)
    if style not in ("full", "line", "off"):
        return Check(WARN, "Hook output", f"gitgotchi.output is '{style}', so full is used", "run `gitgotchi config line` (or full, or off)")
    if style == "off":
        return Check(WARN, "Hook output", "off: commits feed your pet silently", "run `gitgotchi config full` to see it again")
    return Check(OK, "Hook output", style)


def _terminal_checks(console) -> List[Check]:
    from gitgotchi.render.terminal import graphics_protocol

    checks = []
    if not console.is_terminal:
        checks.append(Check(WARN, "Terminal", "output isn't a terminal, so the pet is drawn as one line", "run this in a terminal to see the full pet"))
        return checks

    colors = console.color_system or "none"
    if colors == "truecolor":
        checks.append(Check(OK, "Colors", "true color"))
    else:
        checks.append(Check(WARN, "Colors", f"{colors}: the pet's colors are approximated", "use a true-color terminal (iTerm2, Kitty, WezTerm, Ghostty, VS Code, Windows Terminal), or set COLORTERM=truecolor if yours supports it"))

    encoding = (getattr(sys.stdout, "encoding", "") or "").lower()
    if "utf" not in encoding:
        checks.append(Check(WARN, "Encoding", f"{encoding or 'unknown'}", "set PYTHONIOENCODING=utf-8"))

    width = console.width
    if width < 68:
        checks.append(Check(WARN, "Width", f"{width} columns: the pet is drawn smaller", "widen the window to at least 68 columns"))
    else:
        checks.append(Check(OK, "Width", f"{width} columns"))

    protocol = graphics_protocol()
    checks.append(Check(OK, "Inline images", protocol or "not supported here; `card` saves a PNG instead"))
    return checks


def _api_key_check() -> Check:
    # Never print any part of the key: this output gets pasted into issues
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return Check(OK, "Claude stories", "no ANTHROPIC_API_KEY, so the séance tells its own stories")
    return Check(OK, "Claude stories", "ANTHROPIC_API_KEY is set")


def _hook_python(content: str) -> Optional[str]:
    match = re.search(r"^GITGOTCHI_PYTHON=(.+)$", content, re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        value = value[1:-1].replace("'\"'\"'", "'")
    return value


def _probe(python: str) -> Optional[str]:
    try:
        result = subprocess.run(
            [python, "-c", "import gitgotchi; print(gitgotchi.__version__)"],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _git_config(repo, key: str) -> str:
    try:
        return repo.git.config("--get", key).strip()
    except Exception:
        return ""
