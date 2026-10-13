# Changelog

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

- Initial release for the Kiroween Hackathon.
