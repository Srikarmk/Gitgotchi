"""Terminal UI: the 3D pet scene plus its stats card."""
import random
import sys
import time
from typing import Optional

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gitgotchi.pet import theme
from gitgotchi.pet.states import PetForm, PetMood, PetStats
from gitgotchi.render import HEIGHT, WIDTH, Pose, render_scene
from gitgotchi.render.forms import form_for
from gitgotchi.render.terminal import PixelArt

# Force UTF-8 encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

console = Console(legacy_windows=False)

CARD_WIDTH = 40
FPS = 15


def art_size(available: int) -> tuple:
    """Canvas size that fits the terminal, keeping a 4:3 aspect."""
    width = max(24, min(WIDTH, available))
    width -= width % 2
    return width, int(width * HEIGHT / WIDTH) // 2 * 2


def scene(stats: PetStats, t: float = 0.1, width: int = WIDTH, **kwargs):
    form = form_for(stats.current_form.value)
    w, h = art_size(width)
    return render_scene(
        form, t, w, h, sleeping=stats.current_mood == PetMood.SLEEPING, **kwargs
    )


def bar(value: float, maximum: float, width: int, color: str) -> Text:
    filled = round(max(0.0, min(1.0, value / maximum)) * width)
    text = Text("█" * filled, style=color)
    text.append("░" * (width - filled), style=theme.DIM)
    return text


def stats_card(stats: PetStats) -> Table:
    info = theme.form_info(stats.current_form)
    mood_word, mood_line = theme.MOODS[stats.current_mood]

    heading = Text(f"{stats.pet_name}", style=f"bold {info.color}")
    heading.append(f"  the {info.title}", style=info.color)

    rows = Table.grid(padding=(0, 2))
    rows.add_column(style=theme.DIM, no_wrap=True)
    rows.add_column(no_wrap=True)
    rows.add_row("mood", Text(mood_word, style=theme.ORANGE))
    rows.add_row("quality", Text.assemble(bar(stats.quality_score, 100, 14, theme.GREEN), f" {stats.quality_score:.0f}"))
    level = int(stats.friend_level)
    rows.add_row("friend", Text.assemble(("♥" * level, theme.BLOOD), ("♥" * (10 - level), theme.DIM)))
    rows.add_row("possessed", Text.assemble(bar(stats.possession, 1, 14, theme.CYAN), f" {stats.possession:.0%}"))
    rows.add_row("", "")
    rows.add_row("commits", f"{stats.total_commits}  ({stats.ai_commits} by agents)")
    rows.add_row(
        "lines",
        Text.assemble((f"+{stats.lines_added}", theme.GREEN), " ", (f"-{stats.lines_deleted}", theme.BLOOD)),
    )
    rows.add_row("reverts", str(stats.reverts))

    card = Table.grid()
    card.add_column(width=CARD_WIDTH)
    card.add_row(heading)
    card.add_row(Text(info.blurb, style=f"italic {theme.BONE}"))
    card.add_row("")
    card.add_row(rows)
    card.add_row("")
    card.add_row(Text(f"{stats.pet_name} {mood_line}.", style=theme.DIM))
    return card


def pet_view(stats: PetStats, t: float = 0.1, show_stats: bool = True, **effects) -> Panel:
    info = theme.form_info(stats.current_form)
    side_by_side = show_stats and console.width >= WIDTH + CARD_WIDTH + 8
    art_width = WIDTH if side_by_side or console.width >= WIDTH + 4 else console.width - 4
    art = PixelArt(scene(stats, t, art_width, **effects))

    if not show_stats:
        body = art
    elif side_by_side:
        body = Table.grid(padding=(0, 3))
        body.add_row(art, stats_card(stats))
    else:
        body = Group(art, Text(""), stats_card(stats))

    return Panel(
        body,
        title=Text(f" {info.icon} {stats.pet_name} ", style=f"bold {info.color}"),
        border_style=theme.PURPLE,
        padding=(0, 1),
        expand=False,
    )


def render_pet(stats: PetStats, show_stats: bool = True) -> None:
    console.print(pet_view(stats, show_stats=show_stats))


def animate(frames, fps: int = FPS) -> None:
    """Play a sequence of renderables in place."""
    with Live(console=console, refresh_per_second=fps, transient=False) as live:
        for renderable in frames:
            live.update(renderable)
            time.sleep(1 / fps)


def evolution_frames(stats: PetStats, old_form: PetForm, new_form: PetForm, seconds: float = 2.6):
    """Old form spins up and whites out, then the new form bursts in."""
    count = int(seconds * FPS)
    old_stats, new_stats = _with_form(stats, old_form), _with_form(stats, new_form)
    for i in range(count):
        p = i / (count - 1)
        if p < 0.55:
            k = p / 0.55
            spin = Pose(yaw=(k**2) * 14, bob=0.05 + 0.1 * k)
            yield pet_view(old_stats, t=p, show_stats=False, pose=spin, flash=k * 0.9, sparkles=int(k * 18), seed=i)
        else:
            k = (p - 0.55) / 0.45
            yield pet_view(new_stats, t=p, show_stats=False, flash=max(0.0, 1 - k * 1.6), sparkles=int((1 - k) * 22) + 4, seed=i)


def render_evolution(stats: PetStats, old_form: PetForm, new_form: PetForm) -> None:
    old, new = theme.form_info(old_form), theme.form_info(new_form)
    if console.is_terminal:
        console.print(Text("\n  Something is happening in the repo...", style=f"italic {theme.PURPLE}"))
        animate(evolution_frames(stats, old_form, new_form))
    console.print(
        Text.assemble(
            ("  ✨ ", theme.GOLD),
            (f"{stats.pet_name} evolved: {old.title} {old.icon} → {new.title} {new.icon}", f"bold {new.color}"),
            "\n",
        )
    )


def render_commit_response(
    stats: PetStats,
    lines_added: int,
    lines_deleted: int,
    agent: Optional[str] = None,
) -> None:
    """React to a commit.

    Outside a real terminal (an AI agent running git, CI) this prints a
    single line so it doesn't flood the agent's context.
    """
    if agent:
        line = random.choice(theme.AGENT_REACTIONS).format(name=stats.pet_name, agent=agent)
    else:
        line = random.choice(theme.COMMIT_REACTIONS).format(name=stats.pet_name)
    icon = theme.form_info(stats.current_form).icon

    if not console.is_terminal:
        console.print(f"{icon} gitgotchi: {line} (+{lines_added} -{lines_deleted})")
        return

    console.print(
        Text.assemble(
            (f"\n{icon} {line}  ", theme.ORANGE),
            (f"+{lines_added}", theme.GREEN),
            " ",
            (f"-{lines_deleted}", theme.BLOOD),
        )
    )
    console.print(pet_view(stats, show_stats=False, glitch=bool(agent), seed=stats.total_commits))


def render_message(message: str, style: str = theme.ORANGE) -> None:
    console.print(Text(message, style=style))


def render_error(message: str) -> None:
    console.print(
        Panel(
            Text.assemble(("Something went bump in the night...\n\n", f"bold {theme.ORANGE}"), message),
            border_style=theme.BLOOD,
            title="🕸️  Oops",
            expand=False,
        )
    )


def _with_form(stats: PetStats, form: PetForm) -> PetStats:
    clone = PetStats()
    clone.__dict__.update(stats.__dict__)
    clone.current_form = form
    return clone
