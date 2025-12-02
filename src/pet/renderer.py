"""ASCII art & terminal UI."""
import sys

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.pet.states import PetForm, PetMood, PetStats

# Force UTF-8 encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

console = Console(force_terminal=True, legacy_windows=False)

# ASCII art for each pet form
PET_SPRITES = {
    PetForm.EGG: """
    .-""-.
   /      \\
  |  o  o  |
   \\  __  /
    '-..-'
""",
    PetForm.GHOST: """
    .-.
   (o.o)
    |=|
   __|__
  /     \\
 | () () |
  \\     /
   `---'
""",
    PetForm.ANGEL: """
    \\|/
  .-'o'-.
 /  \\_/  \\
|  (o.o)  |
 \\   |   /
  '--|--'
     |
    / \\
""",
    PetForm.DEMON: """
   /\\ /\\
  (  o.o )
   > ^ <
  /|   |\\
 (_|   |_)
   |   |
  /|   |\\
""",
    PetForm.ZOMBIE: """
    .---.
   /x   x\\
  |  ___  |
   \\ \\_/ /
    |||||
   /|   |\\
  / |   | \\
""",
    PetForm.WRAITH: """
    ___
  .'   '.
 /  o o  \\
|    ^    |
 \\  \\_/  /
  '.___.'
   |||||
  ~~~~~~~
""",
}

# Mood-based colors (Stardew Valley inspired pastels)
MOOD_COLORS = {
    PetMood.JOYFUL: "bright_yellow",  # Gold sparkles
    PetMood.HAPPY: "cyan",  # Sky blue
    PetMood.CONTENT: "bright_white",  # Soft white
    PetMood.HUNGRY: "yellow",  # Gentle yellow
    PetMood.TIRED: "magenta",  # Lavender
    PetMood.SLEEPING: "blue",  # Soft blue
}

# Mood messages (friendly and encouraging)
MOOD_MESSAGES = {
    PetMood.JOYFUL: "✨ Your friend is glowing with happiness! ✨",
    PetMood.HAPPY: "💛 Your companion is content and cheerful!",
    PetMood.CONTENT: "🌟 Your friend is peaceful and happy",
    PetMood.HUNGRY: "🍂 Your friend misses you... time for a commit?",
    PetMood.TIRED: "💤 Your companion is getting sleepy...",
    PetMood.SLEEPING: "😴 Zzz... Your friend is dreaming of code...",
}


def render_pet(stats: PetStats, show_stats: bool = True) -> None:
    """Render pet to terminal with haunted styling.

    Args:
        stats: Current pet statistics
        show_stats: Whether to show detailed stats
    """
    sprite = PET_SPRITES.get(stats.current_form, PET_SPRITES[PetForm.GHOST])
    color = MOOD_COLORS.get(stats.current_mood, "white")
    mood_msg = MOOD_MESSAGES.get(stats.current_mood, "")

    # Create styled sprite
    styled_sprite = Text(sprite, style=color)

    # Build title
    title = f"👻 {stats.current_form.value.upper()} - {stats.current_mood.value}"

    # Build subtitle with mood message
    subtitle = Text(mood_msg, style=color)

    # Create panel content
    content = styled_sprite

    if show_stats:
        stats_text = Text("\n")
        stats_text.append(f"💀 Commits: {stats.total_commits}\n", style="cyan")
        stats_text.append(f"✨ Quality: {stats.quality_score:.1f}/100\n", style="cyan")
        stats_text.append(f"➕ Lines Added: {stats.lines_added}\n", style="green")
        stats_text.append(f"➖ Lines Deleted: {stats.lines_deleted}\n", style="red")
        stats_text.append(f"⚔️  Conflicts: {stats.merge_conflicts}\n", style="yellow")
        stats_text.append(f"🔄 Reverts: {stats.reverts}\n", style="magenta")

        content = Text.assemble(styled_sprite, stats_text)

    # Render panel
    panel = Panel(
        content,
        title=title,
        subtitle=subtitle,
        border_style=color,
        padding=(1, 2),
    )

    console.print(panel)


def render_evolution(old_form: PetForm, new_form: PetForm) -> None:
    """Render evolution animation.

    Args:
        old_form: Previous pet form
        new_form: New pet form
    """
    console.print("\n")
    console.print("✨" * 20, style="bright_yellow")
    console.print(
        f"[bold bright_yellow]Something magical is happening! ✨[/bold bright_yellow]"
    )
    console.print(
        f"[bold bright_cyan]Your {old_form.value} is evolving into a {new_form.value}! 🎉[/bold bright_cyan]"
    )
    console.print("✨" * 20, style="bright_yellow")
    console.print("\n")


def render_commit_response(
    stats: PetStats, lines_added: int, lines_deleted: int
) -> None:
    """Render response to a commit.

    Args:
        stats: Updated pet statistics
        lines_added: Lines added in commit
        lines_deleted: Lines deleted in commit
    """
    console.print("\n")

    # Friendly commit messages
    messages = [
        "Your friend is happy! Great commit! ✨",
        "Yay! Your companion grows stronger! 🌟",
        "Another step forward together! 💛",
        "Your friend appreciates your hard work! 🍂",
        "Wonderful! Your bond deepens! ❤️",
    ]

    import random

    msg = random.choice(messages)
    console.print(f"[cyan]{msg}[/cyan]")

    # Show quick stats
    console.print(
        f"[green]+{lines_added}[/green] [red]-{lines_deleted}[/red] lines"
    )

    # Render pet
    render_pet(stats, show_stats=False)


def render_error(message: str) -> None:
    """Render error with friendly flavor.

    Args:
        message: Error message
    """
    console.print(
        Panel(
            f"[bold yellow]🌙 Oh no! Something went wrong...[/bold yellow]\n\n{message}",
            border_style="yellow",
            title="⚠️  Oops",
        )
    )
