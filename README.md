# 🎃 GitGotchi

[![PyPI](https://img.shields.io/pypi/v/gitgotchi)](https://pypi.org/project/gitgotchi/)
[![CI](https://github.com/Srikarmk/Gitgotchi/actions/workflows/ci.yml/badge.svg)](https://github.com/Srikarmk/Gitgotchi/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/gitgotchi)](https://pypi.org/project/gitgotchi/)

**Your terminal is haunted now.** These days AI agents write a lot of the commits, and GitGotchi is the
little spirit that lives in your repo and watches them land. Feed it commits, keep it company while
your agent works, and see what it grows into.

![All seven forms](https://raw.githubusercontent.com/Srikarmk/Gitgotchi/main/docs/forms.png)

Every form is a real 3D model, raymarched and cel-shaded into pixel art right in your terminal.

## 🚀 Try it

```bash
pip install gitgotchi
gitgotchi demo
```

`demo` opens a throwaway repo where you, Claude and Copilot take turns committing, so you can watch a
pumpkin grow into a Poltergeist in about thirty seconds.

## 🌱 Haunt your own repo

```bash
cd your-project
gitgotchi install   # every commit now feeds your companion
gitgotchi adopt     # raise it on the history you already have
gitgotchi haunt     # open the live pane
```

Keep `gitgotchi haunt` open in a split next to the terminal where you or your agent are working. Every
commit gets a reaction, agent commits glitch the screen, and evolutions play out live. It watches every
local branch, so it sees commits from other worktrees too. Commits that arrive by `git pull` aren't yours,
so they don't feed your companion.

![The haunt pane reacting to commits](https://raw.githubusercontent.com/Srikarmk/Gitgotchi/main/docs/haunt.gif)

## 👾 Possession

GitGotchi spots commits written by AI agents (Claude, Copilot, Codex, Cursor, Devin, Aider, Gemini,
Windsurf, Cline, Amp) from their `Co-Authored-By` trailers, "Generated with" footers and bot accounts.
They feed your companion like any other commit, and they also fill its **possession** meter. Once agents
have written at least half of 6+ commits, your companion becomes a **Poltergeist**.

When git isn't attached to a terminal (an agent running `git commit`, for example), the hook prints a
single line instead of the full pet, so it doesn't flood the agent's context.

## 🖼️ Share it

```bash
gitgotchi card
```

Saves a 1200×630 card, sized for LinkedIn and other link previews:

![A sample card](https://raw.githubusercontent.com/Srikarmk/Gitgotchi/main/docs/card.png)

## 🔮 Séance

```bash
gitgotchi seance
```

Your companion digs through the history for its ghosts: the oldest TODO still in the code, the file
nobody has opened in ages, the biggest deletion, commits made between midnight and 4am, and the first
commit an AI agent wrote. Then it tells you a story about them. Set `ANTHROPIC_API_KEY` (or put it in a
`.env` file) to have Claude tell it; otherwise your companion tells it in its own words. With a key set,
the findings (file names, TODO text and recent commit messages) are sent to the Anthropic API to write the
story. GitGotchi reads only `ANTHROPIC_API_KEY` from `.env` and ignores everything else in it.

## 🎮 All commands

| Command | What it does |
| --- | --- |
| `gitgotchi demo` | Watch a throwaway repo get haunted |
| `gitgotchi install` | Add the post-commit hook (other hooks are kept) |
| `gitgotchi adopt` | Replay existing history (`--reset` to start over) |
| `gitgotchi haunt` | Live pane that reacts to every commit |
| `gitgotchi status` | Your companion and its stats |
| `gitgotchi seance` | Ghost stories from your repo's history |
| `gitgotchi card` | Save a shareable PNG |
| `gitgotchi evolve` | Evolution paths and progress |
| `gitgotchi pet` | Give it some affection |
| `gitgotchi name <name>` | Name your companion |
| `gitgotchi uninstall` | Remove the hook |

## 🌕 Evolution

| Form | How to get there |
| --- | --- |
| 🎃 **Pumpkin** | Where everyone starts |
| 👻 **Ghost** | 3 commits |
| 😇 **Angel** | 6+ commits with quality above 70 |
| 😈 **Demon** | 6+ commits with quality below 30 |
| 👾 **Poltergeist** | 6+ commits, at least half by AI agents |
| 🧟 **Zombie** | 4+ reverts |
| 🌙 **Wraith** | 15+ commits |

Quality drifts toward the score of each commit:

| Factor | Points |
| --- | --- |
| Descriptive message | +15 |
| Conventional commit prefix (`feat:`, `fix:` ...) | +5 |
| Touches tests | +10 |
| Reasonable size | +5 |
| Vague message (`fix`, `wip`, `update code`) | -30 |
| Huge commit (>500 lines) | -15 |
| Revert | -10 |

Go a day without committing and your companion gets hungry; after a week it goes dormant.

## 🖥️ Terminals

GitGotchi draws with true-color half-block characters, so it works in practically every modern terminal,
including VS Code, iTerm2, Kitty, WezTerm, Ghostty, Windows Terminal and macOS Terminal. `gitgotchi card`
also shows the image inline in terminals that support it. Set `GITGOTCHI_GRAPHICS=blocks` to turn that off.

## 🗂️ Where state lives

Your companion lives in `.git/gitgotchi/state.db`, inside the repository's git directory. It never
shows up in `git status`, can't be committed, and every `git worktree` of the repo shares the same pet, so
commits your agents make in their own worktrees count too.

## 🛠️ Development

```bash
git clone https://github.com/Srikarmk/Gitgotchi.git
cd Gitgotchi
pip install -e ".[dev]"
pytest
python scripts/render_assets.py   # regenerate the images in docs/
```

See [INSTALL.md](INSTALL.md) for more and [CHANGELOG.md](CHANGELOG.md) for release notes.

## License

MIT - see [LICENSE](LICENSE).
