# Changelog

## 0.3.2

### Sharper sprites

- Every form is framed bigger, so it gets about 60% more pixels in the same space.
- Shading uses hue-shifted color ramps (cool shadows, warm highlights) lit from the upper front, with
  soft contact shadows, so forms look round instead of striped.
- Glossy highlights on the pumpkin, the Demon and the Poltergeist's keycaps.
- Outlines pick up a little of the color they border, and dark inner lines separate parts that
  overlap (arms, horns, keycaps).
- A cleanup pass removes one-pixel spurs, notches and stray shading pixels.
- The pumpkin's shadows are warm instead of muddy, the Demon has bigger curved horns, and the Angel
  has feathered wings and a halo that stays in frame.

## 0.3.1

### Fixed

- **Security:** GitGotchi loaded every variable from a repo's `.env` file, so a cloned repo could
  inject git settings and run commands during `gitgotchi seance`. Now only `ANTHROPIC_API_KEY` is read.
- AI-agent detection no longer flags people: co-authors at Anthropic, OpenAI or Gemini, anyone named
  Cline, or messages that merely mention ChatGPT. It now matches agent noreply addresses and bot accounts.
- The pet now lives in `.git/gitgotchi/`, so every worktree of a repo shares one pet (agents often
  commit from worktrees). Existing pets are moved there automatically.
- `haunt` watches every local branch, doesn't feed commits that arrive by pull, groups bursts of
  commits into one reaction, keeps running through a busy database, and no longer crashes on
  brackets in commit messages.
- Amending a commit no longer counts it again.
- Running `adopt` while a commit is being processed could lose an update; writes are now atomic.
- `adopt` on an existing pet no longer puts it to sleep.
- The séance handles non-ASCII file names, renamed files, and more TODOs in big repos; the
  witching hour uses each author's own timezone.
- Petting a dormant pet now really wakes it, and friendship grows even while it sleeps.
- The hook works when Python's path contains spaces or shell characters, runs before any `exit` in
  an existing hook, and refuses to edit non-shell hooks.
- Repos in folders with `?` or `%` in their path work.
- `gitgotchi name` rejects empty and very long names; `card` reports the size it actually saved;
  `adopt --limit` must be at least 1.
- Requires `typer>=0.15.4`: older versions crash with current `click`.

## 0.3.0 - Halloween

### New

- **3D pixel-art companion.** Every form is a 3D model, raymarched and cel-shaded into pixel art and
  drawn in the terminal with true-color half blocks. It bobs, blinks and spins, on a night-sky stage.
- **Halloween all year.** Pumpkin replaces Egg, and everything got a new look and voice: cute early
  forms, eerie Demon, Wraith and Poltergeist.
- **Possession.** Commits written by AI agents are recognised from their trailers, footers and bot
  accounts. They fill a possession meter and unlock the new **Poltergeist** form.
- `gitgotchi haunt`: a live pane that reacts to every commit as it lands, with sparkles, possession
  glitches for agent commits, and evolution animations.
- `gitgotchi adopt`: raise your companion on the history a repo already has.
- `gitgotchi card`: a shareable 1200x630 PNG.
- `gitgotchi seance`: ghost stories built from your repo's real history (oldest TODO, forgotten files,
  biggest deletion, late-night commits, the first agent commit). `story` still works as an alias.
- `gitgotchi demo`: watch a throwaway repo get haunted.

### Changed

- The hook prints a single line when git isn't attached to a terminal, so agents running `git commit`
  don't get the full pet in their output.
- Evolution plays an animation in real terminals.
- `numpy` is now a dependency.
- Databases from 0.2.0 are upgraded automatically.

## 0.2.0

### Fixed

- The package is now installed as `gitgotchi` instead of `src`. The old name collided with any
  project that has its own `src/` package and made the post-commit hook fail there.
- `gitgotchi uninstall` now really removes the hook (it used to leave the command behind).
- Running a command from a subdirectory no longer creates a second, empty companion.
- `.gitgotchi/` is excluded from git automatically so the database can't be committed by accident.
- Mood now reflects how long it's been since the last commit when you check on your companion.
- Angel was unreachable; quality is now scored from each commit (see README).
- `gitgotchi story` uses a current Claude model and shows why when it falls back to a built-in story.
- `.env` files are actually loaded.
- `gitgotchi version` reports the real version.

### Changed

- Hooks respect `core.hooksPath` and git worktrees, and are kept alongside any existing hook.
  Running `gitgotchi install` again updates an old hook in place.
- Requires `anthropic>=1.0` and `typer>=0.12`.
- Added `python -m gitgotchi`.

## 0.1.3

- PyPI README update.

## 0.1.0 - 0.1.2

- Initial release.
