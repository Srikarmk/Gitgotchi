---
inclusion: always
---

# Python Code Style Guidelines for GitGotchi

## General Conventions
- Follow PEP 8 style guide
- Use Python 3.10+ features (type hints, match statements)
- Maximum line length: 88 characters (Black formatter standard)
- Use double quotes for strings

## Type Hints
- Always include type hints for function parameters and return values
- Use `from typing import` for complex types
- Example: `def process_commit(commit: Commit) -> dict[str, Any]:`

## Docstrings
- Use triple double-quotes for docstrings
- Follow Google-style docstring format
- Include brief description, Args, Returns, and Raises sections

## Imports
- Group imports: standard library, third-party, local
- Use absolute imports from project root
- Sort alphabetically within groups

## Error Handling
- Use specific exception types
- Provide meaningful error messages
- Log errors using rich console for user-facing messages

## Database
- Use SQLAlchemy ORM models
- Keep database logic in `src/db/`
- Use context managers for sessions

## CLI
- Use Typer for CLI commands
- Use Rich for terminal output and formatting
- Provide helpful error messages and progress indicators

## Git Operations
- Use GitPython for all git interactions
- Handle repository not found errors gracefully
- Validate git state before operations
