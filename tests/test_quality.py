from gitgotchi.pet.quality import (
    is_test_file,
    is_vague,
    score_commit,
    update_quality,
)


def test_vague_messages():
    assert is_vague("fix")
    assert is_vague("WIP")
    assert is_vague("update code.")
    assert not is_vague("Fix crash when config file is missing")


def test_test_file_detection():
    assert is_test_file("tests/test_cli.py")
    assert is_test_file("src/app/__tests__/button.tsx")
    assert is_test_file("pkg/server_test.go")
    assert is_test_file("web/button.spec.ts")
    assert is_test_file("tests\\test_win.py")
    assert not is_test_file("src/contest.py")
    assert not is_test_file("docs/testing.md")


def test_descriptive_commit_beats_vague_commit():
    good = score_commit("feat: add evolution progress bar", 40, ["src/cli.py"])
    bad = score_commit("fix", 40, ["src/cli.py"])
    assert good > 50 > bad


def test_tests_and_size_factors():
    base = score_commit("Add retry logic to the uploader", 40, ["src/up.py"])
    with_tests = score_commit(
        "Add retry logic to the uploader", 40, ["src/up.py", "tests/test_up.py"]
    )
    huge = score_commit("Add retry logic to the uploader", 5000, ["src/up.py"])
    assert with_tests == base + 10
    assert huge == base - 20


def test_score_is_clamped():
    assert score_commit("x", 10_000, [], is_revert=True) >= 0
    assert score_commit(
        "feat: a very descriptive message here", 10, ["tests/test_a.py"]
    ) <= 100


def test_angel_and_demon_are_reachable_in_six_commits():
    quality = 50.0
    for _ in range(6):
        quality = update_quality(quality, score_commit("feat: add x feature", 20, []))
    assert quality > 70

    quality = 50.0
    for _ in range(6):
        quality = update_quality(quality, score_commit("wip", 20, []))
    assert quality < 30
