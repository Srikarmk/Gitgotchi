"""Database migration utilities."""
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db.models import get_engine


class MigrationManager:
    """Handles database schema migrations."""

    def __init__(self, db_path: str = ".gitgotchi/state.db") -> None:
        """Initialize migration manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.engine = get_engine(db_path)

    def get_schema_version(self) -> int:
        """Get current schema version.

        Returns:
            Schema version number, 0 if not set
        """
        try:
            with Session(self.engine) as session:
                result = session.execute(
                    text("SELECT version FROM schema_version LIMIT 1")
                )
                row = result.fetchone()
                return row[0] if row else 0
        except Exception:
            return 0

    def set_schema_version(self, version: int) -> None:
        """Set schema version.

        Args:
            version: Version number to set
        """
        with Session(self.engine) as session:
            # Create table if not exists
            session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
                """
                )
            )

            # Update or insert version
            session.execute(text("DELETE FROM schema_version"))
            session.execute(
                text("INSERT INTO schema_version (version) VALUES (:version)"),
                {"version": version},
            )
            session.commit()

    def backup_database(self) -> Optional[str]:
        """Create backup of database.

        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            db_file = Path(self.db_path)
            if not db_file.exists():
                return None

            backup_path = db_file.with_suffix(".db.backup")
            backup_path.write_bytes(db_file.read_bytes())
            return str(backup_path)
        except Exception:
            return None

    def run_migrations(self) -> None:
        """Run all pending migrations."""
        current_version = self.get_schema_version()

        # Define migrations
        migrations = [
            self._migration_v1_initial,
            # Add future migrations here
        ]

        for version, migration in enumerate(migrations, start=1):
            if version > current_version:
                self.backup_database()
                migration()
                self.set_schema_version(version)

    def _migration_v1_initial(self) -> None:
        """Initial schema - handled by SQLAlchemy create_all."""
        pass
