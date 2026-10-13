"""Spot commits written by AI coding agents."""
import re
from typing import Optional

# (display name, pattern matched against trailers, footers and authors).
# Patterns target agent-specific addresses and bot accounts rather than bare
# names, so a human called Claude or Devin isn't mistaken for an agent.
AGENTS = [
    ("Claude", r"anthropic\.com|claude\[bot\]|\bclaude[ -](code|opus|sonnet|haiku|fable|mythos)\b"),
    ("Copilot", r"\bcopilot\b"),
    ("Codex", r"openai\.com|\bcodex\b|chatgpt"),
    ("Cursor", r"cursoragent|cursor agent|@cursor\.com|cursor\[bot\]"),
    ("Devin", r"devin-ai|devin\.ai|devin\[bot\]"),
    ("Aider", r"aider\.chat|\(aider\)|\baider\b"),
    ("Gemini", r"gemini|google-labs-jules|jules\[bot\]"),
    ("Windsurf", r"windsurf|codeium"),
    ("Cline", r"\bcline\b|roo ?code"),
    ("Amp", r"ampcode\.com"),
]

TRAILER = re.compile(r"^\s*co-authored-by:\s*(?P<who>.+)$", re.IGNORECASE | re.MULTILINE)
GENERATED = re.compile(
    r"(generated|created|written|made) (with|by|using) \[?(?P<who>[\w .-]+)",
    re.IGNORECASE,
)


def _match(text: str) -> Optional[str]:
    for name, pattern in AGENTS:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    return None


def detect_agent(message: str, author_name: str = "", author_email: str = "") -> Optional[str]:
    """Name of the AI agent that wrote a commit, or None for a human commit.

    Looks at Co-Authored-By trailers, "Generated with ..." footers, and the
    author itself (agents like Aider and Copilot's coding agent commit under
    their own names).
    """
    for trailer in TRAILER.finditer(message):
        agent = _match(trailer.group("who"))
        if agent:
            return agent

    footer = GENERATED.search(message)
    if footer:
        agent = _match(footer.group("who"))
        if agent:
            return agent

    if message.lstrip().lower().startswith("aider:"):
        return "Aider"

    return _match(f"{author_name} {author_email}")
