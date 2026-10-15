"""`gitgotchi haunt`: a live pane where the pet reacts to commits as they land.

Meant to sit next to a terminal where you (or an AI agent) are committing.
"""
import random
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque, List, Optional, Set, Tuple

from git import Commit, GitCommandError, Repo
from rich.console import Group
from sqlalchemy.exc import OperationalError
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gitgotchi.db.state_manager import StateManager
from gitgotchi.hooks.installer import has_gitgotchi, hooks_dir
from gitgotchi.hooks.post_commit import feed_commit
from gitgotchi.pet import theme
from gitgotchi.pet.possession import detect_agent
from gitgotchi.pet.quality import commit_subject
from gitgotchi.pet.renderer import CARD_WIDTH, console, scene, stats_card
from gitgotchi.pet.states import PetForm, PetStats
from gitgotchi.render import WIDTH, Pose
from gitgotchi.render.terminal import PixelArt

POLL_SECONDS = 0.5
# Give the post-commit hook a moment to feed the pet before we do it ourselves
HOOK_GRACE_SECONDS = 1.5
LOOP_SECONDS = 4.0
# Reflog entries for commits created locally (not pulled or checked out)
LOCAL_REFLOG_ACTIONS = ("commit", "cherry-pick", "revert")
EVOLUTION_SECONDS = 2.6


@dataclass
class Reaction:
    kind: str  # "commit", "agent" or "evolve"
    text: str
    started: float
    duration: float
    old_form: Optional[PetForm] = None

    def progress(self, now: float) -> float:
        return (now - self.started) / self.duration


class Haunting:
    def __init__(self, repo: Repo, state_manager: StateManager, grace: float = HOOK_GRACE_SECONDS) -> None:
        self.repo = repo
        self.grace = grace
        self.state = state_manager
        self.stats = state_manager.get_pet_state()
        self.tips = self._tips()
        self.pending: List[Tuple[Commit, float]] = []
        self.reactions: Deque[Reaction] = deque()
        self.events = state_manager.get_recent_events(5)
        self.last_poll = 0.0

    def _tips(self) -> Set[str]:
        """Commits at the tip of every local branch and HEAD.

        Watching every branch (not just HEAD) means commits an agent makes in
        another worktree show up too.
        """
        try:
            output = self.repo.git.for_each_ref("--format=%(objectname)", "refs/heads")
        except GitCommandError:
            output = ""
        tips = set(output.split())
        try:
            tips.add(self.repo.head.commit.hexsha)
        except ValueError:  # no commits yet
            pass
        return tips

    def _made_here(self) -> Set[str]:
        """Commits created in this repo (any worktree), according to the reflogs."""
        try:
            output = self.repo.git.reflog("show", "--all", "--format=%H %gs")
        except GitCommandError:
            return set()
        made = set()
        for line in output.splitlines():
            sha, _, subject = line.partition(" ")
            if subject.startswith(LOCAL_REFLOG_ACTIONS):
                made.add(sha)
        return made

    def _hook_installed(self) -> bool:
        hook = hooks_dir(self.repo) / "post-commit"
        return hook.exists() and has_gitgotchi(hook.read_text())

    def _new_commits(self, tips: Set[str]) -> List[Commit]:
        args = ["--reverse", "--max-count=50", *sorted(tips)]
        if self.tips:
            args += ["--not", *sorted(self.tips)]
        try:
            return [self.repo.commit(sha) for sha in self.repo.git.rev_list(*args).split()]
        except GitCommandError:
            return []

    def poll(self, now: float) -> None:
        if now - self.last_poll < POLL_SECONDS:
            return
        self.last_poll = now

        tips = self._tips()
        if tips != self.tips:
            self.pending.extend((c, now) for c in self._new_commits(tips))
            self.tips = tips

        if not self.pending:
            return
        hook = self._hook_installed()
        made_here = None if hook else self._made_here()
        ready, still_pending = [], []
        for commit, seen in self.pending:
            if self.state.has_commit(commit.hexsha):
                ready.append(commit)
            elif now - seen > self.grace:
                # A commit the hook didn't feed, or one the reflog says arrived
                # by pull, merge or checkout, wasn't made here: not the pet's to eat
                if not hook and commit.hexsha in made_here and feed_commit(self.state, commit):
                    ready.append(commit)
            else:
                still_pending.append((commit, seen))
        self.pending = still_pending
        if ready:
            self._react(ready, now)
            self.events = self.state.get_recent_events(5)

    def _react(self, commits: List[Commit], now: float) -> None:
        old_form = self.stats.current_form
        self.stats = self.state.get_pet_state()
        start = max([now] + [r.started + r.duration for r in self.reactions])
        name = self.stats.pet_name

        if self.stats.current_form != old_form:
            old, new = theme.form_info(old_form), theme.form_info(self.stats.current_form)
            text = f"{name} evolved: {old.title} {old.icon} → {new.title} {new.icon}"
            self.reactions.append(Reaction("evolve", text, start, EVOLUTION_SECONDS, old_form))
            return

        agents = [
            detect_agent(c.message, c.author.name or "", c.author.email or "") for c in commits
        ]
        spirits = [a for a in agents if a]
        if len(commits) > 1:
            text = f"{len(commits)} commits landed at once. {name} eats them all"
            if spirits:
                text += f" ({len(spirits)} by agents)"
            self.reactions.append(Reaction("agent" if spirits else "commit", text, start, 1.8))
        elif spirits:
            text = random.choice(theme.AGENT_REACTIONS).format(name=name, agent=spirits[0])
            self.reactions.append(Reaction("agent", text, start, 1.6))
        else:
            text = random.choice(theme.COMMIT_REACTIONS).format(name=name)
            self.reactions.append(Reaction("commit", text, start, 1.3))

    def current(self, now: float) -> Optional[Reaction]:
        while self.reactions and self.reactions[0].progress(now) >= 1:
            self.reactions.popleft()
        if self.reactions and self.reactions[0].progress(now) >= 0:
            return self.reactions[0]
        return None

    def frame(self, now: float):
        t = (now / LOOP_SECONDS) % 1
        reaction = self.current(now)
        side_by_side = console.width >= WIDTH + CARD_WIDTH + 8
        art_width = WIDTH if console.width >= WIDTH + 4 else console.width - 4
        art = PixelArt(self._art(reaction, now, t, art_width))

        if side_by_side:
            top = Table.grid(padding=(0, 3))
            top.add_row(art, stats_card(self.stats))
        else:
            top = Group(art, stats_card(self.stats))

        if reaction:
            color = theme.CYAN if reaction.kind == "agent" else theme.GOLD
            status = Text(f"  {reaction.text}", style=f"bold {color}")
        else:
            dots = "." * (1 + int(now * 2) % 3)
            status = Text(f"  watching for commits{dots}", style=theme.DIM)
            status.append("   ctrl+c to leave", style=theme.DIM)

        repo_name = Path(self.repo.working_tree_dir).name
        return Panel(
            Group(top, Text(""), self._ticker(), Text(""), status),
            title=Text(f" 👻 haunting {repo_name} ", style=f"bold {theme.ORANGE}"),
            border_style=theme.PURPLE,
            padding=(0, 1),
            expand=False,
        )

    def _art(self, reaction: Optional[Reaction], now: float, t: float, width: int):
        if reaction is None:
            return scene(self.stats, t, width)

        p = min(1.0, max(0.0, reaction.progress(now)))
        seed = int(reaction.started * 10)
        if reaction.kind == "evolve":
            if p < 0.55:
                k = p / 0.55
                old = PetStats()
                old.__dict__.update(self.stats.__dict__)
                old.current_form = reaction.old_form
                spin = Pose(yaw=(k**2) * 14, bob=0.05 + 0.1 * k)
                return scene(old, t, width, pose=spin, flash=k * 0.9, sparkles=int(k * 18), seed=seed)
            k = (p - 0.55) / 0.45
            return scene(self.stats, t, width, flash=max(0.0, 1 - k * 1.6), sparkles=int((1 - k) * 22) + 4, seed=seed)

        hop = Pose(yaw=0.4 * (1 - p) * (1 if seed % 2 else -1), bob=0.16 * (1 - (2 * p - 1) ** 2))
        if reaction.kind == "agent":
            return scene(self.stats, t, width, pose=hop, sparkles=int((1 - p) * 10), seed=seed, glitch=p < 0.4)
        return scene(self.stats, t, width, pose=hop, sparkles=int((1 - p) * 14) + 2, seed=seed)

    def _ticker(self) -> Table:
        table = Table.grid(padding=(0, 2))
        table.add_column(no_wrap=True)
        table.add_column(style=theme.DIM, no_wrap=True)
        table.add_column(no_wrap=True, max_width=52, overflow="ellipsis")
        table.add_column(no_wrap=True)

        events = self.events
        if not events:
            table.add_row("", "", Text("No commits yet. Make one and watch.", style=theme.DIM), "")
        for event in events:
            icon = "👾" if event.agent else "🎃"
            who = Text(event.agent, style=theme.CYAN) if event.agent else Text("you", style=theme.ORANGE)
            # Text() so brackets in a commit message aren't read as Rich markup
            table.add_row(icon, _ago(event.timestamp), Text(commit_subject(event.message)), who)
        return table


def _ago(moment: datetime) -> str:
    seconds = (datetime.now() - moment).total_seconds()
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    return f"{int(seconds // 86400)}d ago"


def haunt(repo: Repo, state_manager: StateManager, fps: int = 12, grace: float = HOOK_GRACE_SECONDS) -> None:
    haunting = Haunting(repo, state_manager, grace)
    with Live(console=console, refresh_per_second=fps, screen=True, transient=True) as live:
        try:
            while True:
                now = time.time()
                try:
                    haunting.poll(now)
                except (GitCommandError, OperationalError):
                    # A busy database or a git command mid-rebase; try again next poll
                    pass
                live.update(haunting.frame(now))
                time.sleep(max(0.0, 1 / fps - (time.time() - now)))
        except KeyboardInterrupt:
            pass
