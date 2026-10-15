"""State management for pet persistence."""
from datetime import datetime
from pathlib import Path
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, List, Optional, Sequence

from sqlalchemy import func
from sqlalchemy.orm import Session

from gitgotchi.db.models import (
    CommitHistory,
    PetState,
    StoryMemory,
    get_engine,
    init_db,
)
from gitgotchi.paths import ignore_state_dir, require_repo, state_db_path
from gitgotchi.pet.possession import detect_agent
from gitgotchi.pet.states import PetForm, PetMood, PetStats

if TYPE_CHECKING:
    from gitgotchi.history import HistoryCommit


class StateManager:
    """Manages pet state persistence and retrieval."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize state manager.

        Args:
            db_path: Path to SQLite database file. Defaults to
                .gitgotchi/state.db at the root of the current git repo.
        """
        if db_path is None:
            repo = require_repo()
            ignore_state_dir(repo)
            db_path = str(state_db_path(repo))
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
            stats.created_at = pet_state.created_at
            stats.ai_commits = pet_state.ai_commits or 0

        stats.update_mood()
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
            pet_state.ai_commits = stats.ai_commits
            pet_state.created_at = stats.created_at
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
        agent: Optional[str] = None,
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
            agent: AI agent that wrote the commit, if any
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
                agent=agent,
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

    def has_commit(self, commit_hash: str) -> bool:
        """Check whether a commit has already been processed."""
        with Session(self.engine) as session:
            return (
                session.query(CommitHistory)
                .filter_by(commit_hash=commit_hash)
                .first()
                is not None
            )

    def reset(self) -> None:
        """Start the pet over from a pumpkin, keeping its name."""
        name = self.get_pet_state().pet_name
        with Session(self.engine) as session:
            session.query(CommitHistory).delete()
            session.query(StoryMemory).delete()
            session.query(PetState).delete()
            session.add(PetState(pet_name=name))
            session.commit()

    def replay_history(self, commits: Iterable["HistoryCommit"]) -> "Replay":
        """Feed a batch of past commits (oldest first) in one transaction."""
        stats = self.get_pet_state()
        was_new = stats.total_commits == 0
        with Session(self.engine) as session:
            known = {row[0] for row in session.query(CommitHistory.commit_hash)}

        rows, agents = [], Counter()
        first: Optional[datetime] = None
        for c in commits:
            if c.hexsha in known:
                continue
            known.add(c.hexsha)
            agent = detect_agent(c.message, c.author_name, c.author_email)
            impact = stats.eat_commit(
                c.message, c.lines_added, c.lines_deleted, c.is_merge, c.is_revert,
                c.files, agent, when=c.timestamp,
            )
            if agent:
                agents[agent] += 1
            first = first or c.timestamp
            rows.append(
                CommitHistory(
                    commit_hash=c.hexsha,
                    author=f"{c.author_name} <{c.author_email}>",
                    message=c.message,
                    timestamp=c.timestamp,
                    lines_added=c.lines_added,
                    lines_deleted=c.lines_deleted,
                    files_changed=len(c.files),
                    is_merge=c.is_merge,
                    is_revert=c.is_revert,
                    quality_impact=impact,
                    agent=agent,
                )
            )

        if was_new and first:
            stats.created_at = first
        with Session(self.engine) as session:
            session.add_all(rows)
            session.commit()
        self.save_pet_state(stats)
        stats.update_mood()
        return Replay(stats=stats, count=len(rows), agents=agents, since=first)

    def agent_counts(self) -> Counter:
        """How many tracked commits each AI agent wrote."""
        with Session(self.engine) as session:
            rows = (
                session.query(CommitHistory.agent, func.count())
                .filter(CommitHistory.agent.isnot(None))
                .group_by(CommitHistory.agent)
                .all()
            )
            return Counter(dict(rows))

    def get_recent_events(self, limit: int = 6) -> List[CommitHistory]:
        """Most recent tracked commits, newest first."""
        with Session(self.engine, expire_on_commit=False) as session:
            return (
                session.query(CommitHistory)
                .order_by(CommitHistory.processed_at.desc(), CommitHistory.id.desc())
                .limit(limit)
                .all()
            )

    def get_recent_commits(self, limit: int = 5) -> List[str]:
        """Most recent tracked commit messages, newest first."""
        with Session(self.engine) as session:
            rows = (
                session.query(CommitHistory.message)
                .order_by(CommitHistory.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [row.message for row in rows]

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
        files: Sequence[str] = (),
        agent: Optional[str] = None,
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
            files: Paths touched by the commit
            agent: AI agent that wrote the commit, if any

        Returns:
            Updated PetStats
        """
        stats = self.get_pet_state()
        quality_impact = stats.eat_commit(
            message, lines_added, lines_deleted, is_merge, is_revert, files, agent
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
            agent=agent,
        )

        # Save updated state
        self.save_pet_state(stats)

        return stats


@dataclass
class Replay:
    """Result of replaying history."""

    stats: PetStats
    count: int
    agents: Counter
    since: Optional[datetime]
