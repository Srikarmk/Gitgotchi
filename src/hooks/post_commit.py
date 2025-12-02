"""Git hook handlers."""
from datetime import datetime
from pathlib import Path

from git import Repo

from src.db.state_manager import StateManager
from src.pet.renderer import render_commit_response, render_error, render_evolution


def handle_post_commit() -> None:
    """Handle post-commit hook."""
    try:
        # Get git repo
        repo = Repo(".", search_parent_directories=True)
        git_root = Path(repo.git_dir).parent

        # Get latest commit
        commit = repo.head.commit

        # Parse commit metadata
        commit_hash = commit.hexsha
        author = str(commit.author)
        message = commit.message
        timestamp = datetime.fromtimestamp(commit.committed_date)

        # Calculate stats
        stats = commit.stats.total
        lines_added = stats.get("insertions", 0)
        lines_deleted = stats.get("deletions", 0)
        files_changed = stats.get("files", 0)

        # Check for merge/revert
        is_merge = len(commit.parents) > 1
        is_revert = message.lower().startswith("revert")

        # Initialize state manager
        db_path = git_root / ".gitgotchi" / "state.db"
        state_manager = StateManager(str(db_path))

        # Get old form for evolution check
        old_stats = state_manager.get_pet_state()
        old_form = old_stats.current_form

        # Process commit event
        new_stats = state_manager.process_commit_event(
            commit_hash=commit_hash,
            author=author,
            message=message,
            timestamp=timestamp,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            files_changed=files_changed,
            is_merge=is_merge,
            is_revert=is_revert,
        )

        # Check for evolution
        if new_stats.current_form != old_form:
            render_evolution(old_form, new_stats.current_form)

        # Render commit response
        render_commit_response(new_stats, lines_added, lines_deleted)

    except Exception as e:
        render_error(f"Failed to process commit: {str(e)}")


if __name__ == "__main__":
    handle_post_commit()
