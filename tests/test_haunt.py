import subprocess
from pathlib import Path

from gitgotchi.db.state_manager import StateManager
from gitgotchi.haunt import HOOK_GRACE_SECONDS, Haunting


def commit(repo, message, name="f.py"):
    root = Path(repo.working_tree_dir)
    (root / name).write_text(message)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


def test_haunt_feeds_commits_without_a_hook(repo):
    commit(repo, "feat: before haunting")
    haunting = Haunting(repo, StateManager())

    commit(repo, "feat: while haunting", "g.py")
    haunting.poll(100.0)
    assert haunting.stats.total_commits == 0  # waiting for the hook

    haunting.poll(100.0 + HOOK_GRACE_SECONDS + 1)
    assert haunting.stats.total_commits == 1
    assert haunting.current(100.0 + HOOK_GRACE_SECONDS + 1).kind == "commit"


def test_agent_commit_reaction_and_frame(repo):
    commit(repo, "feat: start")
    haunting = Haunting(repo, StateManager())
    commit(repo, "feat: agent work\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>", "g.py")

    now = 50.0 + HOOK_GRACE_SECONDS + 1
    haunting.poll(50.0)
    haunting.poll(now)

    reaction = haunting.current(now)
    assert reaction.kind == "agent"
    assert "Claude" in reaction.text
    assert haunting.frame(now) is not None


def test_evolution_is_detected(repo):
    commit(repo, "feat: one")
    StateManager()  # the pet exists before haunting starts
    haunting = Haunting(repo, StateManager())
    for i in range(3):
        commit(repo, f"feat: more spooky work {i}", f"x{i}.py")
    now = 10.0 + HOOK_GRACE_SECONDS + 1
    haunting.poll(10.0)
    haunting.poll(now)

    kinds = [r.kind for r in haunting.reactions]
    assert "evolve" in kinds
