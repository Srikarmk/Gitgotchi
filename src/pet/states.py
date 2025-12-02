"""Pet state machine."""
from datetime import datetime
from enum import Enum


class PetMood(Enum):
    """Pet mood states - Stardew Valley inspired friendly moods."""

    JOYFUL = "joyful"  # Recent excellent commit
    HAPPY = "happy"  # Healthy regular activity
    CONTENT = "content"  # Baseline, all is well
    HUNGRY = "hungry"  # No commits in 24h
    TIRED = "tired"  # No commits in 3 days
    SLEEPING = "sleeping"  # No commits in 7 days (can be woken)


class PetForm(Enum):
    """Pet evolution stages - FAST progression for quick feedback."""

    EGG = "egg"  # 0-2 commits
    GHOST = "ghost"  # 3-5 commits (default friendly spirit)
    ANGEL = "angel"  # 6+ commits, quality > 70
    DEMON = "demon"  # 6+ commits, quality < 30 (playful purple, not evil)
    ZOMBIE = "zombie"  # 4+ reverts (cute sleepy, needs coffee)
    WRAITH = "wraith"  # 15+ commits (ultimate ethereal form)


class PetStats:
    """Pet statistics and state."""

    def __init__(self) -> None:
        """Initialize pet with default stats."""
        self.total_commits: int = 0
        self.lines_added: int = 0
        self.lines_deleted: int = 0
        self.merge_conflicts: int = 0
        self.reverts: int = 0
        self.quality_score: float = 50.0
        self.last_fed: datetime = datetime.now()
        self.current_mood: PetMood = PetMood.CONTENT
        self.current_form: PetForm = PetForm.EGG
        self.evolution_points: int = 0
        self.friend_level: int = 1  # 1-10, Stardew Valley style
        self.pet_name: str = "Spirit"

    def update_mood(self) -> None:
        """Update pet mood based on current stats and time."""
        hours_since_fed = (datetime.now() - self.last_fed).total_seconds() / 3600

        if hours_since_fed > 168:  # 7 days
            self.current_mood = PetMood.SLEEPING
        elif hours_since_fed > 72:  # 3 days
            self.current_mood = PetMood.TIRED
        elif hours_since_fed > 24:  # 1 day
            self.current_mood = PetMood.HUNGRY
        elif self.quality_score > 80:
            self.current_mood = PetMood.JOYFUL
        elif self.quality_score > 60:
            self.current_mood = PetMood.HAPPY
        else:
            self.current_mood = PetMood.CONTENT

    def update_form(self) -> None:
        """Update pet form - FAST evolution for quick feedback."""
        # Fast progression: egg → ghost in 2-3 commits
        if self.total_commits <= 2:
            self.current_form = PetForm.EGG
        # Zombie path: lots of reverts (cute sleepy form)
        elif self.reverts >= 4:
            self.current_form = PetForm.ZOMBIE
        # Ultimate form: 15+ commits
        elif self.total_commits >= 15:
            self.current_form = PetForm.WRAITH
        # Advanced forms: 6+ commits
        elif self.total_commits >= 6:
            if self.quality_score > 70:
                self.current_form = PetForm.ANGEL
            elif self.quality_score < 30:
                self.current_form = PetForm.DEMON
            else:
                self.current_form = PetForm.GHOST
        # Default friendly spirit: 3-5 commits
        else:
            self.current_form = PetForm.GHOST

    def feed(self) -> None:
        """Feed the pet (update last_fed timestamp)."""
        self.last_fed = datetime.now()
        self.update_mood()

    def interact(self) -> str:
        """Handle user interaction (pet, talk, play)."""
        # Wake up if sleeping
        if self.current_mood == PetMood.SLEEPING:
            self.current_mood = PetMood.CONTENT
            return "Your friend wakes up! They're happy to see you! ✨"

        # Improve mood slightly
        if self.current_mood == PetMood.TIRED:
            self.current_mood = PetMood.CONTENT
        elif self.current_mood == PetMood.HUNGRY:
            self.current_mood = PetMood.CONTENT

        # Increase friendship
        self.friend_level = min(10, self.friend_level + 0.5)

        responses = [
            "Your friend sparkles with joy! ✨",
            "They float happily around you! 💛",
            "Your companion feels loved! 🌟",
            "Friendship +0.5! Your bond grows stronger! ❤️",
        ]

        import random

        return random.choice(responses)
