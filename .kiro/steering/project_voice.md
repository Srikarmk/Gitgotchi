---
inclusion: always
---

# GitGotchi Development Guidelines

## Visual & Narrative Theme
- **Stardew Valley inspired**: Cozy, friendly, magical pixel art aesthetic
- **Friendly spirits**: Think Junimos, not ghosts from horror movies
- **Warm color palette**: Pastels, soft glows, autumn vibes (pumpkins, leaves, stars)
- **Wholesome magic**: Sparkles, hearts, gentle floating animations
- **Playful not scary**: "Your code needs some love ✨" not "Your code is cursed 💀"

## Code Style
- Python 3.10+ with comprehensive type hints
- Rich library for ALL terminal output (use Rich's color system)
- Use Unicode box-drawing characters and emojis for UI
- Maximum function length: 50 lines
- Descriptive variable names (full words, no abbreviations)
- Docstrings with examples for every public method

## Terminal UI Principles
- Use Rich's Layout for structured displays
- Soft color scheme matching Stardew Valley palette
- Smooth animations using Rich's Live display
- Progress bars should feel magical (sparkles, gentle colors)
- Status indicators use hearts ❤️, stars ⭐, leaves 🍂

## Git Puns & Wordplay
- "Committing to friendship" not "committing to darkness"
- "Branch of memories" not "branch of the undead"
- "Merging paths" not "merge conflict hell"
- "Code spirits" not "code ghosts"
- Keep it light, magical, and encouraging

## Architecture Principles
- State machine for pet behavior (clear, testable)
- All git operations through GitPython (no subprocess)
- Graceful degradation (works offline for local features)
- Local-first: .gitgotchi/state.db stores everything
- Fast startup (< 1 second)

## Error Messages (Friendly Style)
- "Oh no! The spirits can't connect right now... 🌙" (connection error)
- "Hmm, something went wrong with the repository magic ✨" (git error)
- "Your friend is waiting for their first commit! 👻" (no history)
- Always suggest a solution or next step

## Success Messages (Encouraging)
- "Your friend is happy! ✨"
- "Great commit! Your spirit is glowing! 🌟"
- "Level up! Your companion evolved! 🎉"
