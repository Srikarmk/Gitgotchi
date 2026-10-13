"""Main CLI interface."""
import random
from datetime import datetime

import typer
from dotenv import find_dotenv, load_dotenv
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
    load_dotenv(find_dotenv(usecwd=True))
    app()


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
        console.print(Text("Make a commit to wake it up...\n", style=theme.DIM))
    else:
        raise typer.Exit(1)


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


@app.command()
def name(new_name: str):
    """Give your companion a name."""
    try:
        state_manager = load_state()
        pet_stats = state_manager.get_pet_state()

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


@app.command()
def story():
    """Hear a story about your code's history."""
    try:
        from gitgotchi.seance.story_gen import StoryGenerator

        state_manager = load_state()
        pet_stats = state_manager.get_pet_state()

        generator = StoryGenerator()

        context = {
            "total_commits": pet_stats.total_commits,
            "total_lines": pet_stats.lines_added + pet_stats.lines_deleted,
            "days_together": (datetime.now() - pet_stats.created_at).days,
            "recent_commits": state_manager.get_recent_commits(),
        }

        story_text = generator.generate_story(
            "milestone", context, pet_stats.current_form.value
        )

        console.print(
            Panel(
                story_text,
                title=f"📖 {pet_stats.pet_name}'s Story",
                border_style=theme.PURPLE,
                padding=(1, 2),
            )
        )
        if generator.last_error:
            console.print(
                f"[dim](Couldn't reach Claude, so here's a classic story: "
                f"{generator.last_error})[/dim]"
            )

    except typer.Exit:
        raise
    except Exception as e:
        render_error(f"Failed to generate story: {str(e)}")
        raise typer.Exit(1)


@app.command()
def version():
    """Show GitGotchi version."""
    console.print(
        Text(f"🎃 GitGotchi v{__version__}", style=f"bold {theme.ORANGE}")
    )


if __name__ == "__main__":
    app()
