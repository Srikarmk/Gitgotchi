from types import SimpleNamespace

from gitgotchi.seance.story_gen import StoryGenerator


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


def test_no_api_key_uses_fallback(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    gen = StoryGenerator()
    assert gen.generate_story("milestone", {}, "ghost")
    assert gen.last_error is None


def test_reads_text_blocks_after_thinking():
    response = SimpleNamespace(
        stop_reason="end_turn",
        content=[
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text="Once upon a commit..."),
        ],
    )
    messages = FakeMessages(response)
    gen = generator_with(messages)

    story = gen.generate_story("milestone", {"recent_commits": ["feat: x"]}, "ghost")

    assert story == "Once upon a commit..."
    assert "feat: x" in messages.calls[0]["messages"][0]["content"]


def test_refusal_falls_back():
    response = SimpleNamespace(stop_reason="refusal", content=[])
    gen = generator_with(FakeMessages(response))
    assert gen.generate_story("milestone", {}, "ghost")
    assert gen.last_error


def test_api_error_falls_back():
    gen = generator_with(FakeMessages(error=RuntimeError("boom")))
    assert gen.generate_story("milestone", {}, "ghost")
    assert gen.last_error == "boom"
