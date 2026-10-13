"""SQLite schemas."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class PetState(Base):
    """Singleton table storing current pet state (one row per repo)."""

    __tablename__ = "pet_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pet_name: Mapped[str] = mapped_column(String(100), default="Spirit")
    total_commits: Mapped[int] = mapped_column(Integer, default=0)
    lines_added: Mapped[int] = mapped_column(Integer, default=0)
    lines_deleted: Mapped[int] = mapped_column(Integer, default=0)
    merge_conflicts: Mapped[int] = mapped_column(Integer, default=0)
    reverts: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[float] = mapped_column(Float, default=50.0)
    evolution_points: Mapped[int] = mapped_column(Integer, default=0)
    friend_level: Mapped[float] = mapped_column(Float, default=1.0)
    last_fed: Mapped[datetime] = mapped_column(default=datetime.now)
    current_mood: Mapped[str] = mapped_column(String(20), default="content")
    current_form: Mapped[str] = mapped_column(String(20), default="egg")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )


class CommitHistory(Base):
    """Log of all tracked commits."""

    __tablename__ = "commit_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    commit_hash: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    author: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(index=True)
    lines_added: Mapped[int] = mapped_column(Integer, default=0)
    lines_deleted: Mapped[int] = mapped_column(Integer, default=0)
    files_changed: Mapped[int] = mapped_column(Integer, default=0)
    is_merge: Mapped[bool] = mapped_column(default=False)
    is_revert: Mapped[bool] = mapped_column(default=False)
    quality_impact: Mapped[float] = mapped_column(Float, default=0.0)
    processed_at: Mapped[datetime] = mapped_column(default=datetime.now)


class StoryMemory(Base):
    """Cache of generated stories."""

    __tablename__ = "story_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    commit_hash: Mapped[str] = mapped_column(String(40), index=True)
    story_text: Mapped[str] = mapped_column(Text)
    story_type: Mapped[str] = mapped_column(String(50))
    pet_form_at_time: Mapped[str] = mapped_column(String(20))
    pet_mood_at_time: Mapped[str] = mapped_column(String(20))
    generated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


def get_engine(db_path: str = ".gitgotchi/state.db"):
    """Create database engine.

    Args:
        db_path: Path to SQLite database file

    Returns:
        SQLAlchemy engine instance
    """
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_db(db_path: str = ".gitgotchi/state.db") -> None:
    """Initialize database schema.

    Args:
        db_path: Path to SQLite database file
    """
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
