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
- [ ] Hook installer creates post-commit hook
- [ ] Hook calls GitGotchi with commit hash
- [ ] Commit metadata parsed correctly
- [ ] Pet state updates on commit
- [ ] Uninstaller removes hooks cleanly
- [ ] Works with existing git hooks

## Technical Notes
- Check for existing hooks before installing
- Append to existing post-commit if present
- Use shebang for cross-platform compatibility
- Handle git worktrees and submodules
