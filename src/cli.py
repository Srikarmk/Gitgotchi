"""Main CLI interface."""
import typer
from rich.console import Console

from src.db.state_manager import StateManager
from src.hooks.installer import install_hooks, uninstall_hooks
from src.pet.renderer import render_error, render_pet

app = typer.Typer(help="👻 GitGotchi - Your haunted git companion")
console = Console()


@app.command()
def status():
    """Show your pet's current status."""
    try:
        state_manager = StateManager()
        pet_stats = state_manager.get_pet_state()
        render_pet(pet_stats, show_stats=True)
    except Exception as e:
        render_error(f"Failed to load pet state: {str(e)}")
        raise typer.Exit(1)


@app.command()
def install():
    """Install GitGotchi git hooks."""
    if install_hooks():
        console.print(
            "\n[green]🎉 Your repository is now haunted![/green]"
        )
        console.print(
            "[dim]Make a commit to feed your new pet...[/dim]\n"
        )
    else:
        raise typer.Exit(1)


@app.command()
def uninstall():
    """Uninstall GitGotchi git hooks."""
    if uninstall_hooks():
        console.print("\n[yellow]👋 The spirits have departed...[/yellow]\n")
    else:
        raise typer.Exit(1)


@app.command()
def version():
    """Show GitGotchi version."""
    console.print("GitGotchi v0.1.0", style="bold green")


if __name__ == "__main__":
    app()
