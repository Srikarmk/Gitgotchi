"""Git hook handlers."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from git import Commit

from gitgotchi.db.state_manager import StateManager
from gitgotchi.paths import require_repo
from gitgotchi.pet.possession import detect_agent
from gitgotchi.pet.renderer import render_commit_response, render_error, render_evolution
from gitgotchi.pet.states import PetForm, PetStats


@dataclass
class Feeding:
    """What happened when the pet ate a commit."""

    commit_hash: str
    message: str
    agent: Optional[str]
    lines_added: int
    lines_deleted: int
    old_form: PetForm
    stats: PetStats

    @property
    def evolved(self) -> bool:
        return self.stats.current_form != self.old_form


def feed_commit(state_manager: StateManager, commit: Commit) -> Optional[Feeding]:
    """Feed one commit to the pet. Returns None if it was already eaten."""
    if state_manager.has_commit(commit.hexsha):
        return None

    message = commit.message
    commit_stats = commit.stats
    totals = commit_stats.total
    lines_added = totals.get("insertions", 0)
    lines_deleted = totals.get("deletions", 0)
    agent = detect_agent(message, commit.author.name or "", commit.author.email or "")

    old_form = state_manager.get_pet_state().current_form
    stats = state_manager.process_commit_event(
        commit_hash=commit.hexsha,
        author=str(commit.author),
        message=message,
        timestamp=datetime.fromtimestamp(commit.committed_date),
        lines_added=lines_added,
        lines_deleted=lines_deleted,
        files_changed=totals.get("files", 0),
        is_merge=len(commit.parents) > 1,
        is_revert=message.lower().startswith("revert"),
        files=list(commit_stats.files),
        agent=agent,
    )
    return Feeding(commit.hexsha, message, agent, lines_added, lines_deleted, old_form, stats)


def handle_post_commit() -> None:
    """Handle post-commit hook."""
    try:
        repo = require_repo()
        feeding = feed_commit(StateManager(), repo.head.commit)
        if feeding is None:
            return

        if feeding.evolved:
            render_evolution(feeding.stats, feeding.old_form, feeding.stats.current_form)
        else:
            render_commit_response(
                feeding.stats, feeding.lines_added, feeding.lines_deleted, feeding.agent
            )

    except Exception as e:
        render_error(f"Failed to process commit: {str(e)}")


if __name__ == "__main__":
    handle_post_commit()
