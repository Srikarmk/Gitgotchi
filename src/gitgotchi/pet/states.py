"""Pet state machine."""
from datetime import datetime
from enum import Enum
from typing import Optional, Sequence

from gitgotchi.pet.quality import score_commit, update_quality


# How long a visit keeps a starving pet awake
VISIT_HOURS = 6


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
    POLTERGEIST = "poltergeist"  # 6+ commits, mostly written by AI agents


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
        self.friend_level: float = 1.0  # 1-10, Stardew Valley style
        self.pet_name: str = "Spirit"
        self.created_at: datetime = datetime.now()
        self.ai_commits: int = 0
        self.last_visit: Optional[datetime] = None

    @property
    def possession(self) -> float:
        """Share of commits written by AI agents (0-1)."""
        return self.ai_commits / self.total_commits if self.total_commits else 0.0

    def update_mood(self) -> None:
        """Update pet mood based on current stats and time.

        Hunger follows the last commit. A recent visit (`gitgotchi pet`) keeps
        a starving pet awake, though still hungry.
        """
        hours_since_fed = (datetime.now() - self.last_fed).total_seconds() / 3600
        if self.last_visit and (datetime.now() - self.last_visit).total_seconds() < VISIT_HOURS * 3600:
            hours_since_fed = min(hours_since_fed, 72)

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
        # Possessed path: the agents are doing most of the committing
        elif self.total_commits >= 6 and self.possession >= 0.5:
            self.current_form = PetForm.POLTERGEIST
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

    def feed(self, when: Optional[datetime] = None) -> None:
        """Feed the pet (update last_fed timestamp)."""
        self.last_fed = when or datetime.now()
        self.update_mood()

    def eat_commit(
        self,
        message: str,
        lines_added: int = 0,
        lines_deleted: int = 0,
        is_merge: bool = False,
        is_revert: bool = False,
        files: Sequence[str] = (),
        agent: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> float:
        """Update every stat for one commit.

        Returns:
            How much the commit moved the quality score
        """
        self.total_commits += 1
        self.lines_added += lines_added
        self.lines_deleted += lines_deleted
        if is_merge:
            self.merge_conflicts += 1
        if is_revert:
            self.reverts += 1
        if agent:
            self.ai_commits += 1

        # Merge commits just combine existing work, so they don't move quality
        quality_impact = 0.0
        if not is_merge:
            commit_score = score_commit(message, lines_added + lines_deleted, files, is_revert)
            new_quality = update_quality(self.quality_score, commit_score)
            quality_impact = new_quality - self.quality_score
            self.quality_score = new_quality

        self.feed(when)
        self.update_form()
        return quality_impact

    def interact(self) -> bool:
        """Handle user interaction (pet, talk, play).

        Returns:
            True if the pet was woken up
        """
        was_asleep = self.current_mood in (PetMood.SLEEPING, PetMood.TIRED)
        self.last_visit = datetime.now()
        self.friend_level = min(10, self.friend_level + 0.5)
        self.update_mood()
        return was_asleep
