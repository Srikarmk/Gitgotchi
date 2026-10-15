"""Main CLI interface."""
import os
import random
from pathlib import Path
from typing import Optional

import typer
from dotenv import dotenv_values, find_dotenv
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gitgotchi import __version__
from gitgotchi.db.state_manager import StateManager
from gitgotchi.hooks.installer import install_hooks, uninstall_hooks
from gitgotchi.pet import theme
from gitgotchi.pet.renderer import console, pet_view, render_error, render_pet
from gitgotchi.pet.states import PetForm

app = typer.Typer(
    help="🎃 GitGotchi - a little spirit that haunts your git repo",
    no_args_is_help=True,
)


def cli():
    """Entry point for console script."""
    load_api_key()
    app()


def load_api_key() -> None:
    """Pick up ANTHROPIC_API_KEY from a .env file if it isn't already set.

    Only that one variable is read: a repo's .env could otherwise inject
    settings such as GIT_CONFIG_* into the git commands GitGotchi runs.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    path = find_dotenv(usecwd=True)
    key = dotenv_values(path).get("ANTHROPIC_API_KEY") if path else None
    if key:
        os.environ["ANTHROPIC_API_KEY"] = key


def load_state() -> StateManager:
    try:
        return StateManager()
    except Exception as e:
        render_error(str(e))
        raise typer.Exit(1)


@app.command()
def status():
    """Show your companion's current status."""
    try:
        pet_stats = load_state().get_pet_state()
        render_pet(pet_stats, show_stats=True)
    except typer.Exit:
        raise
    except Exception as e:
        render_error(f"Failed to load companion state: {str(e)}")
        raise typer.Exit(1)


@app.command()
def install():
    """Install the git hook so every commit feeds your companion."""
    if install_hooks():
        console.print(
            Text("\n🎃 Your repo is haunted. Every commit will feed your companion.", style=theme.ORANGE)
        )
        if _has_unadopted_history():
            console.print(Text("This repo already has history. Run `gitgotchi adopt` to raise your companion on it.\n", style=theme.DIM))
        else:
            console.print(Text("Make a commit to wake it up...\n", style=theme.DIM))
    else:
        raise typer.Exit(1)


def _has_unadopted_history() -> bool:
    from gitgotchi.paths import find_repo

    repo = find_repo()
    try:
        has_commits = repo is not None and repo.head.is_valid()
        return has_commits and StateManager().get_pet_state().total_commits == 0
    except Exception:
        return False


@app.command()
def uninstall():
    """Remove the GitGotchi git hook."""
    if uninstall_hooks():
        console.print(
            Text("\n🕯️  The haunting is over. Your companion will wait for you here.\n", style=theme.PURPLE)
        )
    else:
        raise typer.Exit(1)


@app.command()
def pet():
    """Pet your companion (boosts mood and friendship)."""
    try:
        state_manager = load_state()
        pet_stats = state_manager.get_pet_state()
        woke = pet_stats.interact()
        state_manager.save_pet_state(pet_stats)

        line = theme.WAKE_REACTION if woke else random.choice(theme.PET_REACTIONS)
        console.print(Text(f"\n💜 {line.format(name=pet_stats.pet_name)}", style=theme.ORANGE))
        console.print(pet_view(pet_stats, show_stats=False, sparkles=8, seed=int(pet_stats.friend_level * 2)))

    except typer.Exit:
        raise
    except Exception as e:
        render_error(f"Failed to interact: {str(e)}")
        raise typer.Exit(1)


MAX_NAME_LENGTH = 30


@app.command()
def name(new_name: str):
    """Give your companion a name."""
    try:
        state_manager = load_state()
        pet_stats = state_manager.get_pet_state()

        new_name = " ".join(new_name.split())
        if not new_name or len(new_name) > MAX_NAME_LENGTH:
            render_error(f"Names need between 1 and {MAX_NAME_LENGTH} characters.")
            raise typer.Exit(1)

        old_name = pet_stats.pet_name
        pet_stats.pet_name = new_name
        state_manager.save_pet_state(pet_stats)

        console.print(Text(f"\n🕯️  Your companion shall be known as {new_name}.", style=theme.ORANGE))
        if old_name != "Spirit":
            console.print(Text(f"(Previously known as {old_name})\n", style=theme.DIM))

    except typer.Exit:
        raise
    except Exception as e:
        render_error(f"Failed to rename companion: {str(e)}")
        raise typer.Exit(1)


EVOLUTION_PATHS = [
    (PetForm.EGG, PetForm.GHOST, "3 commits"),
    (PetForm.GHOST, PetForm.ANGEL, "6 commits with quality above 70"),
    (PetForm.GHOST, PetForm.DEMON, "6 commits with quality below 30"),
    (PetForm.GHOST, PetForm.POLTERGEIST, "6 commits, at least half written by AI agents"),
    (PetForm.GHOST, PetForm.ZOMBIE, "4 reverts"),
    (PetForm.GHOST, PetForm.WRAITH, "15 commits"),
]


@app.command()
def evolve():
    """Check evolution progress and requirements."""
    try:
        pet_stats = load_state().get_pet_state()
        current = theme.form_info(pet_stats.current_form)

        paths = Table.grid(padding=(0, 2))
        for start, end, requirement in EVOLUTION_PATHS:
            info = theme.form_info(end)
            reached = pet_stats.current_form == end
            marker = Text("●" if reached else "○", style=info.color if reached else theme.DIM)
            label = Text(f"{info.icon} {info.title}", style=f"bold {info.color}" if reached else info.color)
            paths.add_row(marker, label, Text(requirement, style=theme.DIM))

        summary = Text.assemble(
            ("Current form  ", theme.DIM), (f"{current.icon} {current.title}\n", f"bold {current.color}"),
            ("Commits       ", theme.DIM), f"{pet_stats.total_commits}\n",
            ("Quality       ", theme.DIM), f"{pet_stats.quality_score:.0f}/100\n",
            ("Possessed     ", theme.DIM), f"{pet_stats.possession:.0%}\n",
            ("Reverts       ", theme.DIM), f"{pet_stats.reverts}\n",
        )
        console.print(
            Panel(
                _stack(summary, paths),
                title="🌕 Evolution",
                border_style=theme.PURPLE,
                expand=False,
            )
        )

    except typer.Exit:
        raise
    except Exception as e:
        render_error(f"Failed to check evolution: {str(e)}")
        raise typer.Exit(1)


def _stack(*renderables):
    grid = Table.grid()
    for r in renderables:
        grid.add_row(r)
    return grid


HAUNTING_ICONS = {"todo": "📜", "forgotten": "🦇", "graveyard": "💀", "witching": "🌙", "spirit": "👾"}


@app.command()
def seance():
    """Hold a séance: dig up your repo's ghosts and hear their story."""
    from gitgotchi.history import read_history
    from gitgotchi.paths import require_repo
    from gitgotchi.seance.hauntings import find_hauntings
    from gitgotchi.seance.story_gen import StoryGenerator

    state_manager = load_state()
    pet_stats = state_manager.get_pet_state()
    repo = require_repo()

    try:
        with console.status(Text("Lighting the candles...", style=theme.PURPLE), spinner="moon"):
            hauntings = find_hauntings(repo, read_history(repo))
            generator = StoryGenerator()
            context = {
                "name": pet_stats.pet_name,
                "repo": Path(repo.working_tree_dir).name,
                "total_commits": pet_stats.total_commits,
                "possession": pet_stats.possession,
                "recent_commits": state_manager.get_recent_commits(),
            }
            story_text = generator.tell(hauntings, context, pet_stats.current_form.value)
    except Exception as e:
        render_error(f"The séance was interrupted: {e}")
        raise typer.Exit(1)

    findings = Table.grid(padding=(0, 1))
    findings.add_column(no_wrap=True)
    findings.add_column(style=f"bold {theme.ORANGE}", no_wrap=True)
    findings.add_column(style=theme.BONE)
    for h in hauntings.items:
        findings.add_row(HAUNTING_ICONS.get(h.kind, "👻"), h.title, h.detail)

    body = [findings, Text(""), Text(story_text, style=f"italic {theme.BONE}")] if hauntings else [Text(story_text, style=f"italic {theme.BONE}")]
    console.print(
        Panel(
            _stack(*body),
            title=Text(f" 🔮 {pet_stats.pet_name}'s séance ", style=f"bold {theme.PURPLE}"),
            border_style=theme.PURPLE,
            padding=(1, 2),
            expand=False,
        )
    )
    if generator.last_error:
        console.print(Text(f"(Couldn't reach Claude, so {pet_stats.pet_name} told this one: {generator.last_error})", style=theme.DIM))
    elif not generator.client:
        console.print(Text("Set ANTHROPIC_API_KEY to have Claude tell the story.", style=theme.DIM))


@app.command(hidden=True)
def story():
    """Alias for seance."""
    seance()


@app.command()
def adopt(
    limit: Optional[int] = typer.Option(None, min=1, help="Only replay the most recent N commits"),
    reset: bool = typer.Option(False, "--reset", help="Start the pet over before replaying"),
):
    """Raise your companion on this repo's existing history."""
    from gitgotchi.history import read_history
    from gitgotchi.paths import require_repo
    from gitgotchi.pet.renderer import animate, evolution_frames

    state_manager = load_state()
    if reset:
        state_manager.reset()

    with console.status(Text("Summoning the spirits of commits past...", style=theme.PURPLE), spinner="moon"):
        history = read_history(require_repo(), limit=limit)
        replay = state_manager.replay_history(history)

    stats = replay.stats
    if not history:
        console.print(Text("\n🕸️  No commits here yet. Make one and your companion will wake up.\n", style=theme.PURPLE))
        return
    if replay.count == 0:
        console.print(Text(f"\n🕯️  {stats.pet_name} has already tasted every commit here.", style=theme.PURPLE))
        console.print(Text("Use --reset to raise it again from a pumpkin.\n", style=theme.DIM))
        return

    if console.is_terminal and stats.current_form != PetForm.EGG:
        animate(evolution_frames(stats, PetForm.EGG, stats.current_form, seconds=3.2))

    since = replay.since.strftime("%b %d, %Y") if replay.since else "the beginning"
    info = theme.form_info(stats.current_form)
    console.print(
        Text.assemble(
            ("\n🎃 Replayed ", theme.DIM),
            (f"{replay.count:,} commit{'s' if replay.count != 1 else ''}", f"bold {theme.ORANGE}"),
            (f" going back to {since}.\n", theme.DIM),
            (f"   {stats.pet_name} grew into a ", theme.DIM),
            (f"{info.title} {info.icon}", f"bold {info.color}"),
            (f"  ·  {stats.possession:.0%} possessed by AI agents", theme.CYAN),
        )
    )
    if replay.agents:
        spirits = "  ·  ".join(f"{name} {count:,}" for name, count in replay.agents.most_common())
        console.print(Text(f"   Spirits in this repo: {spirits}", style=theme.DIM))
    console.print()
    render_pet(stats)


@app.command()
def card(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Where to save it (default gitgotchi-card.png, or .gif with --gif)"),
    scale: int = typer.Option(5, help="Pixel size; 5 gives 1200x630"),
    gif: bool = typer.Option(False, "--gif", help="Save an animated GIF (needs: pip install 'gitgotchi[gif]')"),
):
    """Save a shareable card of your companion."""
    from gitgotchi.paths import require_repo
    from gitgotchi.render.card import make_card, make_card_gif
    from gitgotchi.render.scene import encode_png, upscale
    from gitgotchi.render.terminal import graphics_protocol, inline_image

    state_manager = load_state()
    stats = state_manager.get_pet_state()
    repo_name = Path(require_repo().working_tree_dir).name
    agents = state_manager.agent_counts()
    scale = max(1, min(12, scale))
    output = output or Path("gitgotchi-card.gif" if gif else "gitgotchi-card.png")

    image = make_card(stats, repo_name, agents)
    if gif:
        try:
            data = make_card_gif(stats, repo_name, agents, scale=scale)
        except ImportError:
            render_error("Animated cards need Pillow: pip install 'gitgotchi[gif]'")
            raise typer.Exit(1)
        output.write_bytes(data)
    else:
        output.write_bytes(encode_png(upscale(image, scale)))

    protocol = graphics_protocol()
    if protocol and console.is_terminal:
        console.file.write(inline_image(image, min(console.width - 2, 96), protocol))
        console.file.flush()
    size = f"{image.shape[1] * scale}x{image.shape[0] * scale}"
    console.print(Text(f"\n🖼️  Saved {output} ({size})", style=theme.ORANGE))
    console.print(Text("Share it, and tag the spirits that wrote your code.\n", style=theme.DIM))


@app.command()
def badge(
    output: Path = typer.Option(Path("gitgotchi-badge.svg"), "--output", "-o", help="Where to save the SVG"),
):
    """Save a README badge with your companion's portrait and form."""
    from gitgotchi.render.badge import make_badge

    from gitgotchi.paths import require_repo

    stats = load_state().get_pet_state()
    output.write_text(make_badge(stats), encoding="utf-8")
    root = Path(require_repo().working_tree_dir).resolve()
    try:
        link = output.resolve().relative_to(root).as_posix()
    except ValueError:  # saved outside the repo
        link = output.as_posix()
    console.print(Text(f"\n🏷️  Saved {output}. Commit it and add this to your README:", style=theme.ORANGE))
    console.print(Text(f"[![GitGotchi]({link})](https://github.com/Srikarmk/Gitgotchi)\n", style=theme.BONE))
    console.print(Text("Run `gitgotchi badge` again whenever your companion evolves.\n", style=theme.DIM))


@app.command()
def haunt(fps: int = typer.Option(12, help="Frames per second")):
    """Open a live pane where your companion reacts to every commit.

    Keep it next to the terminal where you (or your AI agent) are working.
    """
    from gitgotchi.haunt import haunt as run_haunt
    from gitgotchi.paths import require_repo

    if not console.is_terminal:
        render_error("haunt needs an interactive terminal.")
        raise typer.Exit(1)
    state_manager = load_state()
    run_haunt(require_repo(), state_manager, fps=max(1, min(30, fps)))
    pet_stats = state_manager.get_pet_state()
    console.print(Text(f"🕯️  {pet_stats.pet_name} drifts back into the repo. See you soon.", style=theme.PURPLE))


@app.command()
def demo():
    """Watch your companion haunt a throwaway repo while AI agents commit to it."""
    from gitgotchi.demo import run_demo

    if not console.is_terminal:
        render_error("demo needs an interactive terminal.")
        raise typer.Exit(1)
    run_demo()
    console.print(Text("🎃 That's GitGotchi. Run `gitgotchi install` in a real repo to adopt your own.", style=theme.ORANGE))


@app.command()
def config(
    output: Optional[str] = typer.Argument(None, help="full, line or off"),
    global_: bool = typer.Option(False, "--global", help="Set it for every repo instead of this one"),
):
    """Choose how much the hook prints after each commit.

    full: the whole pet (default). line: one line. off: nothing.
    Stored in git config as gitgotchi.output.
    """
    from gitgotchi.hooks.post_commit import configured_output
    from gitgotchi.paths import find_repo
    from gitgotchi.pet.renderer import OUTPUT_STYLES

    repo = find_repo()
    if output is None:
        if repo is None:
            render_error("No git repository found here. Run `git init` first.")
            raise typer.Exit(1)
        console.print(Text(f"gitgotchi.output = {configured_output(repo)}", style=theme.ORANGE))
        return

    output = output.strip().lower()
    if output not in OUTPUT_STYLES:
        render_error(f"Pick one of: {', '.join(OUTPUT_STYLES)}")
        raise typer.Exit(1)
    if not global_ and repo is None:
        render_error("No git repository here. Use --global to set it everywhere.")
        raise typer.Exit(1)

    if global_:
        from git import Git

        Git().config("--global", "gitgotchi.output", output)
    else:
        repo.git.config("gitgotchi.output", output)
    where = "every repo" if global_ else "this repo"
    console.print(Text(f"🕯️  Hook output set to {output} for {where}.", style=theme.ORANGE))


@app.command()
def doctor():
    """Check your setup and explain how to fix anything that's wrong."""
    from gitgotchi.doctor import FAIL, WARN, run_checks

    checks = run_checks(console)
    marks = {"ok": ("✓", theme.GREEN), WARN: ("!", theme.ORANGE), FAIL: ("✗", theme.BLOOD)}
    table = Table.grid(padding=(0, 2))
    table.add_column(no_wrap=True)
    table.add_column(no_wrap=True, style="bold")
    table.add_column()
    for check in checks:
        mark, color = marks[check.status]
        detail = Text(check.detail, overflow="fold")
        if check.fix and check.status != "ok":
            detail.append(f"\n→ {check.fix}", style=color)
        table.add_row(Text(mark, style=f"bold {color}"), check.name, detail)
    console.print(Panel(table, title="🩺 GitGotchi doctor", border_style=theme.PURPLE, expand=False))

    failures = [c for c in checks if c.status == FAIL]
    if failures:
        console.print(Text(f"{len(failures)} problem{'s' if len(failures) > 1 else ''} to fix.", style=theme.BLOOD))
        raise typer.Exit(1)
    console.print(Text("Everything needed is working.", style=theme.GREEN))


@app.command()
def statusline(
    plain: bool = typer.Option(False, "--plain", help="No colors (for tmux or Starship)"),
    setup: bool = typer.Option(False, "--setup", help="Show how to add it to Claude Code, tmux and Starship"),
):
    """Print one line about your companion, for status bars and prompts.

    For status bars, use the faster `gitgotchi-statusline` command instead.
    """
    from gitgotchi.statusline import main

    raise typer.Exit(main((["--plain"] if plain else []) + (["--setup"] if setup else [])))


@app.command()
def version():
    """Show GitGotchi version."""
    console.print(
        Text(f"🎃 GitGotchi v{__version__}", style=f"bold {theme.ORANGE}")
    )


if __name__ == "__main__":
    app()
