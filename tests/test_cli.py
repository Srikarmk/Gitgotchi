from typer.testing import CliRunner

from gitgotchi import __version__
from gitgotchi.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_status_in_repo(repo):
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Pumpkin" in result.output


def test_status_outside_repo_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "git init" in result.output


def test_name_and_pet(repo):
    assert runner.invoke(app, ["name", "Pumpkin"]).exit_code == 0
    result = runner.invoke(app, ["pet"])
    assert result.exit_code == 0

    from gitgotchi.db.state_manager import StateManager

    stats = StateManager().get_pet_state()
    assert stats.pet_name == "Pumpkin"
    assert stats.friend_level == 1.5


def test_card_writes_png(repo, tmp_path):
    out = tmp_path / "card.png"
    result = runner.invoke(app, ["card", "--output", str(out), "--scale", "2"])
    assert result.exit_code == 0, result.output
    assert out.read_bytes().startswith(b"\x89PNG")


def test_adopt_on_empty_repo(repo):
    result = runner.invoke(app, ["adopt"])
    assert result.exit_code == 0
    assert "No commits" in result.output


def test_name_is_validated(repo):
    assert runner.invoke(app, ["name", "   "]).exit_code == 1
    assert runner.invoke(app, ["name", "x" * 31]).exit_code == 1
    assert runner.invoke(app, ["name", "  Jack   O  Lantern "]).exit_code == 0

    from gitgotchi.db.state_manager import StateManager

    assert StateManager().get_pet_state().pet_name == "Jack O Lantern"


def test_env_file_only_provides_the_api_key(repo, monkeypatch):
    import os
    from pathlib import Path

    from gitgotchi.cli import load_api_key

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GIT_CONFIG_COUNT", raising=False)
    Path(".env").write_text("ANTHROPIC_API_KEY=test-key\nGIT_CONFIG_COUNT=1\n")

    load_api_key()

    assert os.environ["ANTHROPIC_API_KEY"] == "test-key"
    assert "GIT_CONFIG_COUNT" not in os.environ
