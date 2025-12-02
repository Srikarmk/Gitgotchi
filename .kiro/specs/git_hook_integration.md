# Spec: Git Hook Integration

## Overview
Integrate GitGotchi with git hooks to automatically update pet state on commits.

## Requirements
- Install post-commit hook in `.git/hooks/`
- Hook should call GitGotchi CLI to process commit
- Parse commit metadata (hash, author, message, stats)
- Update pet state based on commit activity
- Handle hook installation and uninstallation

## Deliverables
1. Hook installer in `src/hooks/installer.py`
2. Post-commit handler in `src/hooks/post_commit.py`
3. CLI commands: `gitgotchi install` and `gitgotchi uninstall`
4. Git commit parser using GitPython

## Hook Behavior
- Trigger on every commit
- Extract commit metadata
- Update pet stats (feed, mood, form)
- Show brief pet status in terminal
- Generate story for significant events

## Acceptance Criteria
- [x] Hook installer creates post-commit hook
- [x] Hook calls GitGotchi with commit hash
- [x] Commit metadata parsed correctly
- [x] Pet state updates on commit
- [x] Uninstaller removes hooks cleanly
- [x] Works with existing git hooks

## Implementation Notes
- Hooks installed via `gitgotchi.py install`
- Post-commit hook triggers on every commit
- Parses commit stats using GitPython
- Updates pet state and renders haunted terminal output
- Windows UTF-8 encoding handled properly
- Appends to existing hooks if present

## Technical Notes
- Check for existing hooks before installing
- Append to existing post-commit if present
- Use shebang for cross-platform compatibility
- Handle git worktrees and submodules
