"""State management for pet persistence."""
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import (
    CommitHistory,
    PetState,
    StoryMemory,
    get_engine,
    init_db,
)
from src.pet.states import PetForm, PetMood, PetStats


class StateManager:
    """Manages pet state persistence and retrieval."""

    def __init__(self, db_path: str = ".gitgotchi/state.db") -> None:
        """Initialize state manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_exists()
        self.engine = get_engine(db_path)

    def _ensure_db_exists(self) -> None:
        """Ensure database directory and schema exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        init_db(self.db_path)

    def get_pet_state(self) -> PetStats:
        """Load current pet state from database.

        Returns:
            PetStats instance with current state
        """
        with Session(self.engine) as session:
            pet_state = session.query(PetState).first()

            if not pet_state:
                # Create initial state
                pet_state = PetState()
                session.add(pet_state)
                session.commit()

            # Convert to PetStats
            stats = PetStats()
            stats.pet_name = pet_state.pet_name
            stats.total_commits = pet_state.total_commits
            stats.lines_added = pet_state.lines_added
            stats.lines_deleted = pet_state.lines_deleted
            stats.merge_conflicts = pet_state.merge_conflicts
            stats.reverts = pet_state.reverts
            stats.quality_score = pet_state.quality_score
            stats.evolution_points = pet_state.evolution_points
            stats.friend_level = pet_state.friend_level
            stats.last_fed = pet_state.last_fed
            stats.current_mood = PetMood(pet_state.current_mood)
            stats.current_form = PetForm(pet_state.current_form)

            return stats

    def save_pet_state(self, stats: PetStats) -> None:
        """Save pet state to database.

        Args:
            stats: PetStats instance to persist
        """
        with Session(self.engine) as session:
            pet_state = session.query(PetState).first()

            if not pet_state:
                pet_state = PetState()
                session.add(pet_state)

            pet_state.pet_name = stats.pet_name
            pet_state.total_commits = stats.total_commits
            pet_state.lines_added = stats.lines_added
            pet_state.lines_deleted = stats.lines_deleted
            pet_state.merge_conflicts = stats.merge_conflicts
            pet_state.reverts = stats.reverts
            pet_state.quality_score = stats.quality_score
            pet_state.evolution_points = stats.evolution_points
            pet_state.friend_level = stats.friend_level
            pet_state.last_fed = stats.last_fed
            pet_state.current_mood = stats.current_mood.value
            pet_state.current_form = stats.current_form.value
            pet_state.updated_at = datetime.now()

            session.commit()

    def log_commit(
        self,
        commit_hash: str,
        author: str,
        message: str,
        timestamp: datetime,
        lines_added: int = 0,
        lines_deleted: int = 0,
        files_changed: int = 0,
        is_merge: bool = False,
        is_revert: bool = False,
        quality_impact: float = 0.0,
    ) -> None:
        """Log a commit to history.

        Args:
            commit_hash: Git commit SHA
            author: Commit author
            message: Commit message
            timestamp: Commit timestamp
            lines_added: Lines added in commit
            lines_deleted: Lines deleted in commit
            files_changed: Number of files changed
            is_merge: Whether this is a merge commit
            is_revert: Whether this is a revert commit
            quality_impact: Impact on quality score
        """
        with Session(self.engine) as session:
            # Check if already logged
            existing = (
                session.query(CommitHistory)
                .filter_by(commit_hash=commit_hash)
                .first()
            )

            if existing:
                return

            commit = CommitHistory(
                commit_hash=commit_hash,
                author=author,
                message=message,
                timestamp=timestamp,
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                files_changed=files_changed,
                is_merge=is_merge,
                is_revert=is_revert,
                quality_impact=quality_impact,
            )
            session.add(commit)
            session.commit()

    def save_story(
        self,
        commit_hash: str,
        story_text: str,
        story_type: str,
        pet_form: PetForm,
        pet_mood: PetMood,
        tokens_used: Optional[int] = None,
    ) -> None:
        """Save generated story to cache.

        Args:
            commit_hash: Associated commit hash
            story_text: Generated story content
            story_type: Type of story
            pet_form: Pet form at time of generation
            pet_mood: Pet mood at time of generation
            tokens_used: Number of tokens used
        """
        with Session(self.engine) as session:
            story = StoryMemory(
                commit_hash=commit_hash,
                story_text=story_text,
                story_type=story_type,
                pet_form_at_time=pet_form.value,
                pet_mood_at_time=pet_mood.value,
                tokens_used=tokens_used,
            )
            session.add(story)
            session.commit()

    def get_story(self, commit_hash: str) -> Optional[str]:
        """Retrieve cached story for a commit.

        Args:
            commit_hash: Git commit SHA

        Returns:
            Story text if cached, None otherwise
        """
        with Session(self.engine) as session:
            story = (
                session.query(StoryMemory)
                .filter_by(commit_hash=commit_hash)
                .first()
            )
            return story.story_text if story else None

    def process_commit_event(
        self,
        commit_hash: str,
        author: str,
        message: str,
        timestamp: datetime,
        lines_added: int = 0,
        lines_deleted: int = 0,
        files_changed: int = 0,
        is_merge: bool = False,
        is_revert: bool = False,
    ) -> PetStats:
        """Process a commit event and update pet state.

        Args:
            commit_hash: Git commit SHA
            author: Commit author
            message: Commit message
            timestamp: Commit timestamp
            lines_added: Lines added in commit
            lines_deleted: Lines deleted in commit
            files_changed: Number of files changed
            is_merge: Whether this is a merge commit
            is_revert: Whether this is a revert commit

        Returns:
            Updated PetStats
        """
        # Load current state
        stats = self.get_pet_state()

        # Update stats
        stats.total_commits += 1
        stats.lines_added += lines_added
        stats.lines_deleted += lines_deleted

        if is_merge:
            stats.merge_conflicts += 1

        if is_revert:
            stats.reverts += 1

        # Feed the pet (updates last_fed and mood)
        stats.feed()

        # Update form based on new stats
        stats.update_form()

        # Calculate quality impact
        quality_impact = 0.0
        if is_revert:
            quality_impact = -5.0
        elif is_merge:
            quality_impact = -2.0
        else:
            quality_impact = 1.0

        stats.quality_score = max(
            0.0, min(100.0, stats.quality_score + quality_impact)
        )

        # Log commit
        self.log_commit(
            commit_hash=commit_hash,
            author=author,
            message=message,
            timestamp=timestamp,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            files_changed=files_changed,
            is_merge=is_merge,
            is_revert=is_revert,
            quality_impact=quality_impact,
        )

        # Save updated state
        self.save_pet_state(stats)

        return stats
