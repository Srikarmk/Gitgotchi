from datetime import datetime, timedelta

import pytest

from gitgotchi.pet.states import PetForm, PetMood, PetStats


@pytest.mark.parametrize(
    "commits, quality, reverts, form",
    [
        (0, 50, 0, PetForm.EGG),
        (2, 90, 0, PetForm.EGG),
        (3, 50, 0, PetForm.GHOST),
        (6, 50, 0, PetForm.GHOST),
        (6, 75, 0, PetForm.ANGEL),
        (6, 20, 0, PetForm.DEMON),
        (5, 50, 4, PetForm.ZOMBIE),
        (15, 50, 0, PetForm.WRAITH),
    ],
)
def test_update_form(commits, quality, reverts, form):
    stats = PetStats()
    stats.total_commits = commits
    stats.quality_score = quality
    stats.reverts = reverts
    stats.update_form()
    assert stats.current_form == form


@pytest.mark.parametrize(
    "hours, mood",
    [(1, PetMood.CONTENT), (30, PetMood.HUNGRY), (80, PetMood.TIRED), (200, PetMood.SLEEPING)],
)
def test_update_mood_tracks_time_since_fed(hours, mood):
    stats = PetStats()
    stats.last_fed = datetime.now() - timedelta(hours=hours)
    stats.update_mood()
    assert stats.current_mood == mood


def test_interact_raises_friendship_up_to_ten():
    stats = PetStats()
    for _ in range(50):
        stats.interact()
    assert stats.friend_level == 10
