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


def test_sees_commits_from_other_worktrees(repo, tmp_path):
    commit(repo, "feat: start")
    haunting = Haunting(repo, StateManager())

    worktree = tmp_path / "agent-worktree"
    subprocess.run(["git", "worktree", "add", "-q", str(worktree), "-b", "agent"], cwd=repo.working_tree_dir, check=True)
    (worktree / "w.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "."], cwd=worktree, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "feat: from a worktree\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"],
        cwd=worktree,
        check=True,
    )

    haunting.poll(10.0)
    haunting.poll(10.0 + HOOK_GRACE_SECONDS + 1)
    assert haunting.stats.ai_commits == 1


def test_burst_of_commits_is_one_reaction(repo):
    from gitgotchi.pet.states import PetForm

    commit(repo, "feat: start")
    manager = StateManager()
    stats = manager.get_pet_state()
    stats.total_commits, stats.current_form = 3, PetForm.GHOST
    manager.save_pet_state(stats)
    haunting = Haunting(repo, manager)
    for i in range(5):
        commit(repo, f"feat: burst {i}", f"b{i}.py")

    haunting.poll(10.0)
    haunting.poll(10.0 + HOOK_GRACE_SECONDS + 1)

    assert haunting.stats.total_commits == 8
    assert len(haunting.reactions) == 1
    assert "5 commits" in haunting.reactions[0].text


def test_with_hook_installed_only_hooked_commits_count(repo):
    from gitgotchi.hooks.installer import install_hooks

    install_hooks()
    commit(repo, "feat: fed by the hook")
    haunting = Haunting(repo, StateManager())
    root = Path(repo.working_tree_dir)
    (root / "pulled.py").write_text("x\n")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    # Like a commit that arrived by pull: the hook never runs for it
    subprocess.run(["git", "-c", "core.hooksPath=/nonexistent", "commit", "-q", "-m", "feat: teammate"], cwd=root, check=True)

    haunting.poll(10.0)
    haunting.poll(10.0 + HOOK_GRACE_SECONDS + 1)

    assert haunting.stats.total_commits == 1
    assert not haunting.reactions


def test_pulled_commits_are_not_fed_without_a_hook(repo, tmp_path):
    commit(repo, "feat: start")
    upstream = tmp_path / "upstream"
    subprocess.run(["git", "clone", "-q", repo.working_tree_dir, str(upstream)], check=True)
    for i in range(3):
        (upstream / f"t{i}.py").write_text("x\n")
        subprocess.run(["git", "add", "."], cwd=upstream, check=True)
        subprocess.run(["git", "-c", "user.name=Bob", "-c", "user.email=b@x.com", "commit", "-q", "-m", f"feat: bob {i}"], cwd=upstream, check=True)

    haunting = Haunting(repo, StateManager())
    branch = repo.active_branch.name
    subprocess.run(["git", "pull", "-q", "--ff-only", str(upstream), branch], cwd=repo.working_tree_dir, check=True)

    haunting.poll(10.0)
    haunting.poll(10.0 + HOOK_GRACE_SECONDS + 1)
    assert haunting.stats.total_commits == 0
