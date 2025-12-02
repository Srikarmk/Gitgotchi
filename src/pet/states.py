"""Pet state machine."""
from datetime import datetime
from enum import Enum
from typing import Optional


class PetMood(Enum):
    """Pet mood states based on recent activity."""

    ECSTATIC = "ecstatic"  # Recent good commits
    HAPPY = "happy"  # Healthy activity
    NEUTRAL = "neutral"  # Baseline
    HUNGRY = "hungry"  # No commits in 24h
    SICK = "sick"  # Merge conflicts, failed builds
    DYING = "dying"  # No activity in 7 days
    POSSESSED = "possessed"  # Special: bad code quality


class PetForm(Enum):
    """Pet evolution stages."""

    EGG = "egg"  # 0-10 commits
    GHOST = "ghost"  # 11-50 commits (neutral path)
    ANGEL = "angel"  # 50+ commits, good quality
    DEMON = "demon"  # 50+ commits, chaos
    ZOMBIE = "zombie"  # Lots of reverts
    WRAITH = "wraith"  # Advanced form


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
        self.current_mood: PetMood = PetMood.NEUTRAL
        self.current_form: PetForm = PetForm.EGG

    def update_mood(self) -> None:
        """Update pet mood based on current stats and time."""
        hours_since_fed = (datetime.now() - self.last_fed).total_seconds() / 3600

        if hours_since_fed > 168:  # 7 days
            self.current_mood = PetMood.DYING
        elif self.quality_score < 30:
            self.current_mood = PetMood.POSSESSED
        elif self.merge_conflicts > 5:
            self.current_mood = PetMood.SICK
        elif hours_since_fed > 24:
            self.current_mood = PetMood.HUNGRY
        elif self.quality_score > 80:
            self.current_mood = PetMood.ECSTATIC
        elif self.quality_score > 60:
            self.current_mood = PetMood.HAPPY
        else:
            self.current_mood = PetMood.NEUTRAL

    def update_form(self) -> None:
        """Update pet form based on commit history and behavior."""
        if self.total_commits <= 10:
            self.current_form = PetForm.EGG
        elif self.reverts > 20:
            self.current_form = PetForm.ZOMBIE
        elif self.total_commits > 100 and self.quality_score > 70:
            self.current_form = PetForm.WRAITH
        elif self.total_commits > 50:
            if self.quality_score > 70:
                self.current_form = PetForm.ANGEL
            else:
                self.current_form = PetForm.DEMON
        else:
            self.current_form = PetForm.GHOST

    def feed(self) -> None:
        """Feed the pet (update last_fed timestamp)."""
        self.last_fed = datetime.now()
        self.update_mood()
