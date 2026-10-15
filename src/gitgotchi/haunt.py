"""`gitgotchi haunt`: a live pane where the pet reacts to commits as they land.

Meant to sit next to a terminal where you (or an AI agent) are committing.
"""
import random
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, List, Optional, Tuple

from git import Commit, Repo
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gitgotchi.db.state_manager import StateManager
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
        self.head = self._head()
        self.pending: List[Tuple[Commit, float]] = []
        self.reactions: Deque[Reaction] = deque()
        self.last_poll = 0.0

    def _head(self) -> Optional[str]:
        try:
            return self.repo.head.commit.hexsha
        except ValueError:  # no commits yet
            return None

    def poll(self, now: float) -> None:
        if now - self.last_poll < POLL_SECONDS:
            return
        self.last_poll = now

        head = self._head()
        if head and head != self.head:
            if self.head:
                new = list(self.repo.iter_commits(f"{self.head}..{head}", max_count=50))
            else:
                new = [self.repo.head.commit]
            self.pending.extend((c, now) for c in reversed(new))
            self.head = head

        still_pending = []
        for commit, seen in self.pending:
            if self.state.has_commit(commit.hexsha):
                self._react(commit, now)
            elif now - seen > self.grace:
                feed_commit(self.state, commit)
                self._react(commit, now)
            else:
                still_pending.append((commit, seen))
        self.pending = still_pending

    def _react(self, commit: Commit, now: float) -> None:
        old_form = self.stats.current_form
        self.stats = self.state.get_pet_state()
        start = max([now] + [r.started + r.duration for r in self.reactions])
        name = self.stats.pet_name

        if self.stats.current_form != old_form:
            old, new = theme.form_info(old_form), theme.form_info(self.stats.current_form)
            text = f"{name} evolved: {old.title} {old.icon} → {new.title} {new.icon}"
            self.reactions.append(Reaction("evolve", text, start, EVOLUTION_SECONDS, old_form))
            return

        agent = detect_agent(commit.message, commit.author.name or "", commit.author.email or "")
        if agent:
            text = random.choice(theme.AGENT_REACTIONS).format(name=name, agent=agent)
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

        repo_name = self.repo.working_tree_dir.rstrip("/").split("/")[-1]
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

        events = self.state.get_recent_events(5)
        if not events:
            table.add_row("", "", Text("No commits yet. Make one and watch.", style=theme.DIM), "")
        for event in events:
            icon = "👾" if event.agent else "🎃"
            who = Text(event.agent, style=theme.CYAN) if event.agent else Text("you", style=theme.ORANGE)
            table.add_row(icon, _ago(event.timestamp), commit_subject(event.message), who)
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
                haunting.poll(now)
                live.update(haunting.frame(now))
                time.sleep(max(0.0, 1 / fps - (time.time() - now)))
        except KeyboardInterrupt:
            pass
