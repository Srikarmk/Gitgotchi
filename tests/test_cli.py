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
