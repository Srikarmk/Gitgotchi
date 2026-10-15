import subprocess
from pathlib import Path

from typer.testing import CliRunner

from gitgotchi.cli import app
from gitgotchi.hooks.installer import install_hooks

runner = CliRunner()


def commit(repo, message, name="f.py"):
    root = Path(repo.working_tree_dir)
    (root / name).write_text(message)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    return subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True, capture_output=True, text=True)


def test_config_output_off_silences_the_hook(repo):
    install_hooks()
    assert runner.invoke(app, ["config", "off"]).exit_code == 0
    result = commit(repo, "feat: quiet please")
    assert (result.stdout + result.stderr).strip() == ""

    assert runner.invoke(app, ["config", "line"]).exit_code == 0
    result = commit(repo, "feat: one line please", "g.py")
    assert len((result.stdout + result.stderr).strip().splitlines()) == 1


def test_config_rejects_unknown_styles(repo):
    assert runner.invoke(app, ["config", "loud"]).exit_code == 1


def test_doctor_passes_with_a_working_hook_and_fails_with_a_broken_one(repo):
    install_hooks()
    assert runner.invoke(app, ["doctor"]).exit_code == 0

    hook = Path(repo.git_dir) / "hooks" / "post-commit"
    content = hook.read_text().splitlines()
    hook.write_text("\n".join("GITGOTCHI_PYTHON='/nonexistent/python'" if line.startswith("GITGOTCHI_PYTHON=") else line for line in content) + "\n")
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "no longer exists" in result.output


def test_doctor_never_shows_the_api_key(repo, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret-value-1234")
    result = runner.invoke(app, ["doctor"])
    assert "1234" not in result.output and "secret" not in result.output


def test_badge_is_an_svg_with_a_portrait(repo, tmp_path):
    out = tmp_path / "badge.svg"
    result = runner.invoke(app, ["badge", "-o", str(out)])
    assert result.exit_code == 0, result.output
    svg = out.read_text()
    assert svg.startswith("<svg") and "Pumpkin" in svg and svg.count("<rect") > 20


def test_badges_inlined_together_do_not_share_a_clip_path():
    from gitgotchi.pet.states import PetForm, PetStats
    from gitgotchi.render.badge import make_badge

    a, b = PetStats(), PetStats()
    b.current_form = PetForm.DEMON
    b.total_commits, b.ai_commits = 10, 3
    ids = {make_badge(s).split('clipPath id="')[1].split('"')[0] for s in (a, b)}
    assert len(ids) == 2


def test_animated_card(repo, tmp_path):
    import pytest

    pytest.importorskip("PIL")
    out = tmp_path / "card.gif"
    result = runner.invoke(app, ["card", "--gif", "--scale", "1", "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert out.read_bytes()[:6] == b"GIF89a"
