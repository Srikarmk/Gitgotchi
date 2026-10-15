"""`gitgotchi demo`: a throwaway repo where you and some AI agents commit
while the pet haunts it."""
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from git import Repo

from gitgotchi.db.state_manager import StateManager
from gitgotchi.haunt import haunt

CLAUDE = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
COPILOT = "Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>"

SCRIPT = [
    ("pumpkin.py", "feat: carve the first pumpkin", None),
    ("candle.py", "feat: light a candle inside the pumpkin", CLAUDE),
    ("tests/test_candle.py", "test: make sure the candle stays lit", None),
    ("lantern.py", "feat: hang a haunted lantern on the porch", CLAUDE),
    ("walls.py", "fix: ghosts no longer walk through walls", COPILOT),
    ("bats.py", "feat: summon a friendly bat colony", CLAUDE),
    ("SPELLBOOK.md", "docs: write down every spell in the spellbook", None),
    ("crypt.py", "refactor: tidy up the crypt", CLAUDE),
    ("tests/test_bats.py", "test: count the bats at midnight", CLAUDE),
    ("cauldron.py", "feat: make the cauldron bubble", COPILOT),
]


def _commit(root: Path, path: str, message: str, trailer) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"# {message}\nSPOOKY = True\n")
    body = f"{message}\n\n{trailer}" if trailer else message
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", body], cwd=root, check=True, capture_output=True)


def run_demo(interval: float = 2.8, fps: int = 12) -> None:
    root = Path(tempfile.mkdtemp(prefix="gitgotchi-demo-"))
    cwd = os.getcwd()
    stop = threading.Event()
    state = None
    worker = None
    try:
        repo = Repo.init(root)
        with repo.config_writer() as cw:
            cw.set_value("user", "name", "You")
            cw.set_value("user", "email", "you@example.com")
            cw.set_value("commit", "gpgsign", "false")
        os.chdir(root)
        state = StateManager()
        stats = state.get_pet_state()
        stats.pet_name = "Pumpkin"
        state.save_pet_state(stats)

        def committer():
            if stop.wait(2.0):
                return
            for path, message, trailer in SCRIPT:
                _commit(root, path, message, trailer)
                if stop.wait(interval):
                    return

        worker = threading.Thread(target=committer, daemon=True)
        worker.start()
        haunt(Repo(root), state, fps=fps, grace=0.2)
    finally:
        stop.set()
        if worker:
            worker.join(timeout=10)  # let a commit in progress finish
        if state:
            state.close()  # Windows can't delete an open database
        os.chdir(cwd)
        shutil.rmtree(root, ignore_errors=True)
