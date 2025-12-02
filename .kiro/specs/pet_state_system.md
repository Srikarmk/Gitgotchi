# Spec: Pet State System

## Overview
Implement persistent pet state management with SQLAlchemy models and state transition logic.

## Data Model
Create SQLAlchemy models for:
- PetState (singleton table, one row per repo)
- CommitHistory (log of all tracked commits)
- StoryMemory (cache of generated stories)

## State Machine Logic
Implement state transitions:
- Commit → feed pet, improve mood, update stats
- Time decay → hunger increases over time
- Quality analysis → affects evolution path
- Merge conflict → sick state

## Persistence
- Save state after every git event
- Load state on CLI startup
- Migration strategy for schema changes

## Requirements
- SQLAlchemy 2.0+ with type hints
- SQLite database stored in `.gitgotchi/state.db`
- Context managers for session handling
- Automatic schema creation on first run

## Deliverables
1. Database models in `src/db/models.py`
2. State manager in `src/db/state_manager.py`
3. Migration utilities in `src/db/migrations.py`
4. Integration with pet state machine

## Acceptance Criteria
- [x] PetState model with all stats fields
- [x] CommitHistory model with git metadata
- [x] StoryMemory model for caching
- [x] StateManager class for CRUD operations
- [x] Automatic database initialization
- [x] State transitions working correctly
- [x] Time-based mood decay implemented

## Implementation Notes
- Database stored in `.gitgotchi/state.db`
- StateManager handles all CRUD operations with context managers
- `process_commit_event()` method handles full state transition logic
- Quality score adjusts based on commit type (revert -5, merge -2, normal +1)
- Automatic schema creation on first run
- Migration system in place for future schema changes
