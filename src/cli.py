"""Main CLI interface."""
import typer
from rich.console import Console
from rich.panel import Panel

from src.db.state_manager import StateManager
from src.hooks.installer import install_hooks, uninstall_hooks
from src.pet.renderer import render_error, render_pet

app = typer.Typer(help="✨ GitGotchi - Your friendly dev companion")
console = Console()


def cli():
    """Entry point for console script."""
    app()


@app.command()
def status():
    """Show your companion's current status."""
    try:
        state_manager = StateManager()
        pet_stats = state_manager.get_pet_state()
        render_pet(pet_stats, show_stats=True)
    except Exception as e:
        render_error(f"Failed to load companion state: {str(e)}")
        raise typer.Exit(1)


@app.command()
def install():
    """Install GitGotchi git hooks for automatic feeding."""
    if install_hooks():
        console.print(
            "\n[green]✨ Git hooks installed! Your companion will be fed automatically on commits.[/green]"
        )
        console.print("[dim]Make a commit to meet your new friend...[/dim]\n")
    else:
        raise typer.Exit(1)


@app.command()
def uninstall():
    """Remove GitGotchi git hooks."""
    if uninstall_hooks():
        console.print(
            "\n[yellow]👋 Git hooks removed. You can still feed manually with 'gitgotchi feed'.[/yellow]\n"
        )
    else:
        raise typer.Exit(1)


@app.command()
def pet():
    """Pet your companion (boosts mood slightly)."""
    try:
        state_manager = StateManager()
        pet_stats = state_manager.get_pet_state()

        # Interact with pet
        message = pet_stats.interact()

        # Save updated state
        state_manager.save_pet_state(pet_stats)

        # Show response
        console.print(Panel(message, border_style="cyan", title="💛 Interaction"))
        render_pet(pet_stats, show_stats=False)

    except Exception as e:
        render_error(f"Failed to interact: {str(e)}")
        raise typer.Exit(1)


@app.command()
def name(new_name: str):
    """Give your companion a name."""
    try:
        state_manager = StateManager()
        pet_stats = state_manager.get_pet_state()

        old_name = pet_stats.pet_name
        pet_stats.pet_name = new_name

        state_manager.save_pet_state(pet_stats)

        console.print(
            f"\n[green]✨ Your companion is now named {new_name}![/green]"
        )
        if old_name != "Spirit":
            console.print(f"[dim](Previously known as {old_name})[/dim]\n")

    except Exception as e:
        render_error(f"Failed to rename companion: {str(e)}")
        raise typer.Exit(1)


@app.command()
def evolve():
    """Check evolution progress and requirements."""
    try:
        state_manager = StateManager()
        pet_stats = state_manager.get_pet_state()

        # Calculate progress
        current_form = pet_stats.current_form.value
        commits = pet_stats.total_commits
        quality = pet_stats.quality_score

        console.print(
            Panel(
                f"""[cyan]Current Form:[/cyan] {current_form}
[cyan]Total Commits:[/cyan] {commits}
[cyan]Quality Score:[/cyan] {quality:.1f}/100
[cyan]Friend Level:[/cyan] {"❤️" * int(pet_stats.friend_level)} ({pet_stats.friend_level}/10)

[yellow]Evolution Requirements:[/yellow]
• Egg → Ghost: 3 commits (you have {commits})
• Ghost → Angel: 6 commits + quality > 70
• Ghost → Demon: 6 commits + quality < 30
• Any → Zombie: 4 reverts (you have {pet_stats.reverts})
• Any → Wraith: 15 commits (ultimate form!)
""",
                title="🌟 Evolution Progress",
                border_style="cyan",
            )
        )

    except Exception as e:
        render_error(f"Failed to check evolution: {str(e)}")
        raise typer.Exit(1)


@app.command()
def story():
    """Hear a story about your code's history."""
    try:
        from src.seance.story_gen import StoryGenerator

        state_manager = StateManager()
        pet_stats = state_manager.get_pet_state()

        generator = StoryGenerator()

        # Generate milestone story
        context = {
            "total_commits": pet_stats.total_commits,
            "total_lines": pet_stats.lines_added + pet_stats.lines_deleted,
            "days_together": (
                pet_stats.last_fed - pet_stats.last_fed
            ).days,  # Simplified
        }

        story_text = generator.generate_story(
            "milestone", context, pet_stats.current_form.value
        )

        console.print(
            Panel(
                story_text,
                title=f"📖 {pet_stats.pet_name}'s Story",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    except Exception as e:
        render_error(f"Failed to generate story: {str(e)}")
        raise typer.Exit(1)


@app.command()
def version():
    """Show GitGotchi version."""
    console.print(
        "GitGotchi v0.1.0 - Your friendly dev companion ✨", style="bold cyan"
    )


if __name__ == "__main__":
    app()
