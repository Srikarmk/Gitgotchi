from datetime import datetime, timedelta
from types import SimpleNamespace

from gitgotchi.seance.hauntings import Haunting, Hauntings
from gitgotchi.seance.story_gen import StoryGenerator

HAUNTINGS = Hauntings(
    [
        Haunting(
            "todo",
            "The oldest unfinished business",
            'app.py:3  "TODO: fix later"',
            datetime.now() - timedelta(days=400),
            {"path": "app.py", "line": "3", "note": "TODO: fix later"},
        ),
        Haunting(
            "spirit",
            "The first spirit",
            'Claude wrote "feat: x"',
            datetime.now() - timedelta(days=20),
            {"agent": "Claude", "subject": "feat: x"},
        ),
    ]
)
CONTEXT = {"name": "Boo", "recent_commits": ["feat: x"], "possession": 0.5}


class FakeMessages:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def generator_with(messages):
    gen = StoryGenerator(api_key=None)
    gen.client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    return gen


def test_offline_story_uses_findings(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    gen = StoryGenerator()
    story = gen.tell(HAUNTINGS, CONTEXT, "ghost")
    assert "In app.py, line 3" in story
    assert "1 year" in story
    assert gen.last_error is None


def test_offline_story_for_empty_repo():
    story = StoryGenerator(api_key=None).tell(Hauntings(), CONTEXT, "egg")
    assert "too new" in story


def test_prompt_includes_findings_and_tone():
    response = SimpleNamespace(
        stop_reason="end_turn",
        content=[
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text="Once upon a commit..."),
        ],
    )
    messages = FakeMessages(response)
    gen = generator_with(messages)

    story = gen.tell(HAUNTINGS, CONTEXT, "wraith")

    assert story == "Once upon a commit..."
    prompt = messages.calls[0]["messages"][0]["content"]
    assert "Tone: eerie" in prompt
    assert "TODO: fix later" in prompt
    assert messages.calls[0]["model"] == "claude-opus-5-5"


def test_refusal_falls_back():
    gen = generator_with(FakeMessages(SimpleNamespace(stop_reason="refusal", content=[])))
    assert "app.py" in gen.tell(HAUNTINGS, CONTEXT, "ghost")
    assert gen.last_error


def test_api_error_falls_back():
    gen = generator_with(FakeMessages(error=RuntimeError("boom")))
    assert gen.tell(HAUNTINGS, CONTEXT, "ghost")
    assert gen.last_error == "boom"
