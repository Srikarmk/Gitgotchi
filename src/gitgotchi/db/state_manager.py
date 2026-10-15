"""State management for pet persistence."""
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
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
from gitgotchi.paths import require_repo, state_db_path
from gitgotchi.pet.possession import detect_agent
from gitgotchi.pet.states import PetForm, PetMood, PetStats

if TYPE_CHECKING:
    from gitgotchi.history import HistoryCommit


class StateManager:
    """Manages pet state persistence and retrieval."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize state manager.

        Args:
            db_path: Path to SQLite database file. Defaults to the pet of
                the git repo containing the current directory.
        """
        if db_path is None:
            db_path = str(state_db_path(require_repo()))
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = get_engine(db_path)
        init_db(self.engine)

    def close(self) -> None:
        """Release the database file (needed before deleting it on Windows)."""
        self.engine.dispose()

    @staticmethod
    def _row(session: Session) -> PetState:
        pet_state = session.query(PetState).first()
        if pet_state is None:
            pet_state = PetState()
            session.add(pet_state)
            session.flush()
        return pet_state

    @staticmethod
    def _to_stats(pet_state: PetState) -> PetStats:
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
        stats.last_visit = pet_state.last_visit
        stats.current_mood = PetMood(pet_state.current_mood)
        stats.current_form = PetForm(pet_state.current_form)
        stats.created_at = pet_state.created_at
        stats.ai_commits = pet_state.ai_commits or 0
        return stats

    @staticmethod
    def _write(pet_state: PetState, stats: PetStats) -> None:
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
        pet_state.last_visit = stats.last_visit
        pet_state.current_mood = stats.current_mood.value
        pet_state.current_form = stats.current_form.value
        pet_state.updated_at = datetime.now()

    def get_pet_state(self) -> PetStats:
        """Load current pet state from database.

        Returns:
            PetStats instance with current state
        """
        with Session(self.engine) as session:
            stats = self._to_stats(self._row(session))
            session.commit()

        stats.update_mood()
        return stats

    def save_pet_state(self, stats: PetStats) -> None:
        """Save pet state to database.

        Args:
            stats: PetStats instance to persist
        """
        with Session(self.engine) as session:
            self._write(self._row(session), stats)
            session.commit()

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
        rows, agents = [], Counter()
        first: Optional[datetime] = None
        with Session(self.engine) as session:
            pet_state = self._row(session)
            stats = self._to_stats(pet_state)
            was_new = stats.total_commits == 0
            last_fed = stats.last_fed
            known = {row[0] for row in session.query(CommitHistory.commit_hash)}

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

            if not was_new:
                # Old history mustn't make a pet that was fed today look starved
                stats.last_fed = max(stats.last_fed, last_fed)
            elif first:
                stats.created_at = first
            session.add_all(rows)
            self._write(pet_state, stats)
            session.commit()

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

    def replace_commit(self, old_hash: str, new_hash: str, message: str) -> bool:
        """Point a tracked commit at its amended version.

        Returns:
            False if the old commit was never tracked
        """
        with Session(self.engine) as session:
            row = session.query(CommitHistory).filter_by(commit_hash=old_hash).first()
            if row is None:
                return False
            row.commit_hash = new_hash
            row.message = message
            session.commit()
            return True

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
        with Session(self.engine) as session:
            pet_state = self._row(session)
            stats = self._to_stats(pet_state)

            # Checked inside the same locked transaction, so the hook and
            # haunt can't both count a commit
            seen = session.query(CommitHistory.id).filter_by(commit_hash=commit_hash).first()
            if seen:
                session.commit()
                stats.update_mood()
                return stats

            quality_impact = stats.eat_commit(
                message, lines_added, lines_deleted, is_merge, is_revert, files, agent
            )
            session.add(
                CommitHistory(
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
            )
            self._write(pet_state, stats)
            session.commit()

        return stats


@dataclass
class Replay:
    """Result of replaying history."""

    stats: PetStats
    count: int
    agents: Counter
    since: Optional[datetime]
