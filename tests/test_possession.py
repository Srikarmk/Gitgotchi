import pytest

from gitgotchi.pet.possession import detect_agent


@pytest.mark.parametrize(
    "message, author, email, agent",
    [
        ("feat: x\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>", "", "", "Claude"),
        ("fix: y\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)", "", "", "Claude"),
        ("feat: z\n\nCo-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>", "", "", "Copilot"),
        ("feat: a\n\nCo-authored-by: Cursor Agent <cursoragent@cursor.com>", "", "", "Cursor"),
        ("Add thing", "devin-ai-integration[bot]", "158243242+devin-ai-integration[bot]@users.noreply.github.com", "Devin"),
        ("aider: refactor parser", "Sam", "sam@example.com", "Aider"),
        ("Tidy up", "google-labs-jules[bot]", "jules@example.com", "Gemini"),
    ],
)
def test_detects_agents(message, author, email, agent):
    assert detect_agent(message, author, email) == agent


@pytest.mark.parametrize(
    "message, author, email",
    [
        ("feat: pair\n\nCo-authored-by: Claude Martin <claude@acme.com>", "Devin Smith", "devin@acme.com"),
        ("Bump lodash from 4.17.20 to 4.17.21", "dependabot[bot]", "49699333+dependabot[bot]@users.noreply.github.com"),
        ("fix: plain human commit", "Srikar", "s@example.com"),
    ],
)
def test_humans_and_other_bots_are_not_agents(message, author, email):
    assert detect_agent(message, author, email) is None
