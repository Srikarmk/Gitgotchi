# 🎃 GitGotchi - Your Friendly Dev Companion 👻

[![PyPI](https://img.shields.io/pypi/v/gitgotchi)](https://pypi.org/project/gitgotchi/)
[![CI](https://github.com/Srikarmk/Gitgotchi/actions/workflows/ci.yml/badge.svg)](https://github.com/Srikarmk/Gitgotchi/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/gitgotchi)](https://pypi.org/project/gitgotchi/)

A Stardew Valley X Halloween-inspired terminal companion that lives in your git repository!

## ✨ Features

- Adorable ASCII companion that evolves based on your coding habits
- Fed automatically through a git post-commit hook
- Warm, AI-generated stories about your code history (optional)
- Friendship system inspired by Stardew Valley
- Fast evolution - see changes every 2-3 commits!

## 🚀 Installation

```bash
pip install gitgotchi
```

Requires Python 3.10+ and git. [pipx](https://pipx.pypa.io) works too: `pipx install gitgotchi`.

## 🌱 Quick Start

```bash
cd your-project
gitgotchi install   # add the post-commit hook
gitgotchi status    # meet your companion!
```

Then just commit as usual - your companion eats every commit.

## 🎮 Commands

| Command | What it does |
| --- | --- |
| `gitgotchi status` | See your companion and their stats |
| `gitgotchi pet` | Give them affection (boosts mood and friendship) |
| `gitgotchi story` | Hear a story about your code |
| `gitgotchi evolve` | Check evolution progress and requirements |
| `gitgotchi name <name>` | Give your companion a name |
| `gitgotchi install` | Install the git hook |
| `gitgotchi uninstall` | Remove the git hook (other hooks are left alone) |
| `gitgotchi version` | Show the installed version |

## 🌟 Evolution Forms

- 🥚 **Egg** (0-2 commits) - starting form
- 👻 **Ghost** (3-5 commits) - default friendly spirit
- 👼 **Angel** (6+ commits, quality > 70) - high quality path
- 😈 **Demon** (6+ commits, quality < 30) - chaotic but playful path
- 🧟 **Zombie** (4+ reverts) - needs coffee
- 🌙 **Wraith** (15+ commits) - ultimate ethereal form

## 📈 Commit Quality

Every commit gets a score, and your companion's quality score drifts toward it:

| Factor | Points |
| --- | --- |
| Descriptive message | +15 |
| Conventional commit prefix (`feat:`, `fix:` ...) | +5 |
| Touches tests | +10 |
| Reasonable size | +5 |
| Vague message (`fix`, `wip`, `update code`) | -30 |
| Huge commit (>500 lines) | -15 |
| Revert | -10 |

Merge commits don't affect quality.

## 📖 Stories (optional)

`gitgotchi story` works out of the box with built-in stories. To get stories written by Claude
from your actual commit history, set an Anthropic API key:

```bash
export ANTHROPIC_API_KEY='your-key-here'
# or put it in a .env file in your project
echo "ANTHROPIC_API_KEY=your-key-here" >> .env
```

## 🗂️ Where state lives

Your companion is stored in `.gitgotchi/state.db` at the root of the repository. GitGotchi adds
`.gitgotchi/` to `.git/info/exclude`, so it never shows up in `git status` and is never committed.

## 🎨 Theme

GitGotchi is inspired by Stardew Valley's cozy, friendly aesthetic. Your companion is a warm,
magical spirit - not scary! Think Junimos, sparkles, and autumn leaves.

## 🛠️ Development

```bash
git clone https://github.com/Srikarmk/Gitgotchi.git
cd Gitgotchi
pip install -e ".[dev]"
pytest
```

See [INSTALL.md](INSTALL.md) for more and [CHANGELOG.md](CHANGELOG.md) for release notes.

## License

MIT - see [LICENSE](LICENSE).
