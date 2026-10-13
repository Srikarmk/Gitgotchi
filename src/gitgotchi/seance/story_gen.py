"""Ghost stories about your code, told by Claude (or by the pet itself offline)."""
import os
import random
from typing import Dict, Optional

from anthropic import Anthropic

from gitgotchi.seance.hauntings import Hauntings

MODEL = "claude-opus-5-5"

EERIE_FORMS = {"demon", "wraith", "poltergeist"}


class StoryGenerator:
    """Generate short Halloween stories about a repo's history."""

    SYSTEM_PROMPT = """You are the spirit companion that haunts a developer's git
repository, telling a short ghost story about their code at a séance.

Write for a terminal:
- Two short paragraphs, under 120 words total
- Plain text only: no markdown, headings, bullet points or emoji
- Use the specific findings you are given (file names, dates, counts), and
  don't invent facts beyond them
- Playful Halloween imagery: candles, crypts, cobwebs, pumpkins, spirits
- Gently teasing, never mean about the developer's work
- End with one line that nudges them back to coding

Match the tone you are asked for: "cute" is cozy and sweet, "eerie" is
spooky and a little ominous, but still fun."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize story generator.

        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None
        self.last_error: Optional[str] = None

    def tell(self, hauntings: Hauntings, context: Dict, pet_form: str) -> str:
        """Tell a séance story about the hauntings found in the repo."""
        if not self.client:
            return self._offline_story(hauntings, context, pet_form)

        try:
            message = self.client.beta.messages.create(
                model=MODEL,
                max_tokens=16000,
                output_config={"effort": "low"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": self._prompt(hauntings, context, pet_form)}],
            )

            if message.stop_reason == "refusal":
                self.last_error = "the request was declined"
                return self._offline_story(hauntings, context, pet_form)

            text = "".join(
                block.text for block in message.content if block.type == "text"
            ).strip()
            return text or self._offline_story(hauntings, context, pet_form)

        except Exception as e:
            self.last_error = str(e)
            return self._offline_story(hauntings, context, pet_form)

    def _prompt(self, hauntings: Hauntings, context: Dict, pet_form: str) -> str:
        tone = "eerie" if pet_form in EERIE_FORMS else "cute"
        lines = []
        for h in hauntings.items:
            age = h.age_days()
            when = f" ({age} days ago)" if age is not None else ""
            lines.append(f"- {h.title}: {h.detail}{when}")
        findings = "\n".join(lines) or "- Nothing yet. The repo is brand new and quiet."
        recent = "\n".join(f"- {m}" for m in context.get("recent_commits", [])) or "- (none)"

        return f"""Tone: {tone}
You are {context.get('name', 'Spirit')}, currently a {pet_form}.
Repository: {context.get('repo', 'this repo')}
Total commits: {context.get('total_commits', 0)}
Share written by AI agents: {context.get('possession', 0):.0%}

What the séance uncovered:
{findings}

Most recent commit messages:
{recent}"""

    def _offline_story(self, hauntings: Hauntings, context: Dict, pet_form: str) -> str:
        """A story stitched together from the findings, for when Claude isn't available."""
        found = hauntings.by_kind()
        name = context.get("name", "Spirit")
        eerie = pet_form in EERIE_FORMS
        opener = random.choice(
            [
                "The candles flicker as the séance begins.",
                "Somewhere in the repo, a floorboard creaks.",
                "The moon is out, and the commit log is whispering.",
            ]
            if eerie
            else [
                "Gather round the jack-o'-lantern, friend.",
                "Pull up a pumpkin. Story time.",
                "The candles are lit and the cocoa is warm.",
            ]
        )

        beats = []
        if "todo" in found:
            h, f = found["todo"], found["todo"].facts
            beats.append(
                f'In {f["path"]}, line {f["line"]}, a note has waited {_days(h)}: "{f["note"]}". It still hopes someone will finish it.'
            )
        if "forgotten" in found:
            h = found["forgotten"]
            beats.append(f"Nobody has opened {h.facts['path']} in {_days(h)}. Cobwebs are forming.")
        if "graveyard" in found:
            f = found["graveyard"].facts
            beats.append(f'{f["lines"]:,} lines lie buried in the graveyard of "{f["subject"]}". May they rest in peace.')
        if "witching" in found:
            f = found["witching"].facts
            count = f["count"]
            beats.append(
                f"{count} commit{'s were' if count != 1 else ' was'} made between midnight and 4am, the latest at {f['latest']}. Someone was up very late."
            )
        if "spirit" in found:
            h, f = found["spirit"], found["spirit"].facts
            beats.append(
                f'The first spirit arrived {_days(h)} ago, when {f["agent"]} wrote "{f["subject"]}". The keyboard hasn\'t been the same since.'
            )

        if not beats:
            return f"{opener} {name} looks around... but this repo is too new to be haunted. Make a few commits, and come back when there are ghosts to talk about."

        random.shuffle(beats)
        first, rest = beats[:2], beats[2:]
        closer = (
            f"{name} leans closer. \"Now. Back to work, before the next spirit commits for you.\""
            if eerie
            else f"{name} smiles. \"Every ghost here started as a commit. Let's make another.\""
        )
        story = " ".join([opener] + first)
        if rest:
            story += "\n\n" + " ".join(rest) + " " + closer
        else:
            story += "\n\n" + closer
        return story


def _days(h) -> str:
    days = h.age_days() or 0
    if days == 0:
        return "less than a day"
    if days >= 365:
        years = days // 365
        return f"{years} year{'s' if years > 1 else ''}"
    if days >= 30:
        return f"{days // 30} month{'s' if days >= 60 else ''}"
    return f"{days} day{'s' if days != 1 else ''}"
