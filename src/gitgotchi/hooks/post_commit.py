"""Git hook handlers."""
from datetime import datetime

from gitgotchi.db.state_manager import StateManager
from gitgotchi.paths import require_repo
from gitgotchi.pet.possession import detect_agent
from gitgotchi.pet.renderer import render_commit_response, render_error, render_evolution


def handle_post_commit() -> None:
    """Handle post-commit hook."""
    try:
        repo = require_repo()
        commit = repo.head.commit
        state_manager = StateManager()

        # Never count the same commit twice (e.g. the hook being re-run by hand)
        if state_manager.has_commit(commit.hexsha):
            return

        # Parse commit metadata
        commit_hash = commit.hexsha
        author = str(commit.author)
        message = commit.message
        timestamp = datetime.fromtimestamp(commit.committed_date)

        # Calculate stats
        commit_stats = commit.stats
        stats = commit_stats.total
        lines_added = stats.get("insertions", 0)
        lines_deleted = stats.get("deletions", 0)
        files_changed = stats.get("files", 0)
        files = list(commit_stats.files)

        # Check for merge/revert
        is_merge = len(commit.parents) > 1
        is_revert = message.lower().startswith("revert")

        # Get old form for evolution check
        old_stats = state_manager.get_pet_state()
        old_form = old_stats.current_form

        # Process commit event
        agent = detect_agent(message, commit.author.name or "", commit.author.email or "")
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
            files=files,
            agent=agent,
        )

        # Check for evolution
        if new_stats.current_form != old_form:
            render_evolution(new_stats, old_form, new_stats.current_form)
        else:
            render_commit_response(new_stats, lines_added, lines_deleted, agent)

    except Exception as e:
        render_error(f"Failed to process commit: {str(e)}")


if __name__ == "__main__":
    handle_post_commit()
