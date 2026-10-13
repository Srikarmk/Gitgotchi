"""LLM story generation with Claude."""
import os
import random
from typing import Dict, Optional

from anthropic import Anthropic


class StoryGenerator:
    """Generate warm, friendly stories about code history using Claude AI."""

    SYSTEM_PROMPT = """You are a friendly spirit companion from a cozy pixel game 
like Stardew Valley. You live in a developer's git repository and tell warm, 
encouraging stories about their code history.

Your personality:
- Warm and supportive (never critical or scary)
- Playful and gentle (use sparkles ✨, hearts ❤️, leaves 🍂)
- Wise but humble (you're learning about code alongside them)
- Encouraging (celebrate all progress, big and small)

Your stories should:
- Be 2-4 short paragraphs
- Include specific details from the code history
- End with a gentle question or encouragement
- Use soft, magical language
- Make the developer feel good about their work

Avoid:
- Technical jargon (keep it accessible)
- Criticism or judgment
- Scary or dark themes
- Overwhelming detail
"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize story generator.

        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None

    def generate_story(
        self, story_type: str, context: Dict, pet_form: str
    ) -> str:
        """Generate a story using Claude.

        Args:
            story_type: Type of story (forgotten_todo, milestone, etc.)
            context: Relevant git data
            pet_form: Current companion form

        Returns:
            Friendly story text (2-4 paragraphs)
        """
        if not self.client:
            return self._get_fallback_story(story_type)

        try:
            prompt = self._build_story_prompt(story_type, context, pet_form)

            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            return message.content[0].text

        except Exception:
            return self._get_fallback_story(story_type)

    def get_daily_message(self, state: Dict) -> str:
        """Get a warm daily message based on current state.

        Args:
            state: Current pet state

        Returns:
            Encouraging message
        """
        messages = [
            "Good morning! Ready to write some code together? ✨",
            "Hello friend! What shall we build today? 🌟",
            "A new day, a fresh start! I'm excited to see what you create! 💛",
            "Your companion is here and ready to help! 🍂",
            "Time to make some magic happen! ✨",
        ]

        return random.choice(messages)

    def get_evolution_message(self, old_form: str, new_form: str) -> str:
        """Special message for evolution events.

        Args:
            old_form: Previous form
            new_form: New form

        Returns:
            Celebratory message
        """
        messages = {
            ("egg", "ghost"): "Your friend has hatched! Welcome to the world, little spirit! ✨",
            ("ghost", "angel"): "Your dedication shines bright! Your companion has become an angel! 👼",
            ("ghost", "demon"): "Chaos can be fun! Your companion embraces their playful side! 😈💜",
            ("ghost", "zombie"): "Your friend needs coffee! They've become a sleepy zombie! ☕💚",
            "wraith": "Ultimate form achieved! Your companion is now an ethereal wraith! 🌙✨",
        }

        key = (old_form, new_form)
        if key in messages:
            return messages[key]
        elif new_form == "wraith":
            return messages["wraith"]

        return f"Your {old_form} evolved into a {new_form}! How wonderful! 🎉"

    def _build_story_prompt(
        self, story_type: str, context: Dict, pet_form: str
    ) -> str:
        """Build prompt for Claude based on story type and context."""
        prompts = {
            "milestone": f"""
Tell a celebratory story about reaching a coding milestone.

Details:
- Total commits: {context.get('total_commits', 0)}
- Lines of code: {context.get('total_lines', 0)}
- Time coding together: {context.get('days_together', 0)} days

Make it feel like a celebration of progress and friendship.
End with encouragement for the journey ahead.
            """,
            "first_commit": f"""
Tell a warm welcome story about the first commit in this repository.

Details:
- Commit message: "{context.get('message', '')}"
- Date: {context.get('date', 'recently')}

Make it feel like the beginning of a wonderful adventure together.
            """,
            "encouragement": """
Tell a gentle, encouraging story about the value of consistent effort.

Make the developer feel appreciated for their work, no matter how small.
Remind them that every commit is progress.
            """,
        }

        return prompts.get(story_type, prompts["encouragement"])

    def _get_fallback_story(self, story_type: str) -> str:
        """Return pre-written story when API unavailable."""
        fallback_stories = {
            "milestone": [
                "Look how far we've come together! Every commit is a step forward, and you've taken so many. I'm proud to be your companion on this journey! 🌟",
                "Congratulations on all your hard work! From that first commit to now, we've built something special together. Here's to many more adventures! ✨",
            ],
            "encouragement": [
                "Every line of code is a step forward. You're doing great! 💛",
                "Progress isn't always visible, but I see how hard you work! Keep going! ✨",
                "Even small commits make a difference. Your dedication inspires me! 🌟",
            ],
            "first_commit": [
                "Welcome! This is the beginning of something wonderful. I'm so happy to be here with you! ✨",
                "A new adventure begins! Every great project starts with a single commit. Let's build something amazing together! 💛",
            ],
        }

        stories = fallback_stories.get(
            story_type, fallback_stories["encouragement"]
        )
        return random.choice(stories)
