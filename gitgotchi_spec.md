# GitGotchi: Haunted Dev Companion - Complete Build Spec

## 🎃 Project Overview

GitGotchi is a terminal-based companion pet that lives in your git repository. It's a Stardew Valley-inspired friendly ghost that feeds on your commits, tells stories about your code's history, and evolves based on your development patterns. Think cute pixel art spirits, not scary horror.

## 🎨 Visual Theme: Stardew Valley Pixel Spirits

### Art Direction
- Friendly, rounded pixel art ghosts (16x16 or 32x32 sprites)
- Soft, pastel color palette (lavender, mint green, soft blue, pale pink)
- Bouncy animations and sparkle effects
- Cozy autumn/Halloween aesthetic (pumpkins, leaves, soft glows)
- Inspired by Stardew Valley's Junimos and friendly spirits
- NO scary elements - everything should feel warm and magical

### Color Palette
- Ghost base: Soft white with gentle transparency effect (#F0F0FF)
- Angel form: Pale gold with sparkles (#FFE5B4)
- Demon form: Playful purple with tiny horns (#C8A2C8)
- Zombie form: Mint green, cute and sleepy (#B4E7CE)
- Wraith form: Ethereal blue with shimmer (#B0C4DE)

### Animation Style
- Gentle floating/bobbing motion
- Sparkle particles when happy
- Soft color shifts based on mood
- Cozy emotes (hearts, stars, zzz for sleep)

## 📁 Project Structure

```
gitgotchi/
├── .kiro/                          # Kiro configuration (MUST COMMIT THIS!)
│   ├── specs/
│   │   ├── 01_pet_state_system.md
│   │   ├── 02_git_analyzer.md
│   │   ├── 03_terminal_ui.md
│   │   ├── 04_story_generator.md
│   │   └── 05_git_hooks.md
│   ├── hooks/
│   │   └── pre_commit_check.sh
│   └── steering/
│       └── project_voice.md
├── src/
│   ├── __init__.py
│   ├── pet/
│   │   ├── __init__.py
│   │   ├── states.py              # State machine
│   │   ├── renderer.py            # Terminal UI rendering
│   │   ├── evolution.py           # Evolution logic
│   │   └── animations.py          # Animation frames
│   ├── seance/
│   │   ├── __init__.py
│   │   ├── git_analyzer.py        # Git history parser
│   │   ├── story_generator.py     # LLM story generation
│   │   ├── quality.py             # Code quality scoring
│   │   └── patterns.py            # Pattern detection
│   ├── hooks/
│   │   ├── __init__.py
│   │   ├── post_commit.py         # Git hook handlers
│   │   └── installer.py           # Hook installation
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py              # SQLAlchemy models
│   │   └── database.py            # DB initialization
│   └── cli.py                     # Main CLI interface
├── assets/
│   └── sprites/
│       ├── ghost_happy.txt        # ASCII/Unicode sprites
│       ├── ghost_hungry.txt
│       ├── angel_happy.txt
│       └── ...
├── tests/
│   ├── test_states.py
│   ├── test_git_analyzer.py
│   └── test_story_generator.py
├── .env.example
├── .gitignore
├── requirements.txt
├── setup.py
└── README.md
```

## 🎯 Kiro Steering Document

**File: `.kiro/steering/project_voice.md`**

```markdown
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
- Local-first: .gitgotchi.db stores everything
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
```

---

## 📋 Spec 1: Pet State System

**File: `.kiro/specs/01_pet_state_system.md`**

```markdown
# Spec: Pet State System

## Overview
Implement the core state machine and database models for the GitGotchi companion.

## Database Models (SQLAlchemy)

**File: `src/db/models.py`**

### PetState Table (Singleton - one per repository)
```python
class PetState(Base):
    __tablename__ = 'pet_state'
    
    id: int  # Primary key
    repo_path: str  # Absolute path to git repository
    pet_name: str  # User-chosen name (default: "Spirit")
    
    # Current status
    current_form: str  # egg, ghost, angel, demon, zombie, wraith
    current_mood: str  # joyful, happy, content, hungry, tired, sleeping
    
    # Statistics
    total_commits: int = 0
    total_lines_added: int = 0
    total_lines_deleted: int = 0
    merge_conflicts_resolved: int = 0
    reverts_count: int = 0
    quality_score: float = 50.0  # 0-100
    
    # Timestamps
    last_commit_time: datetime
    last_interaction_time: datetime
    created_at: datetime
    updated_at: datetime
    
    # Evolution progress
    evolution_points: int = 0  # Points toward next form
    friend_level: int = 1  # 1-10, Stardew Valley style friendship
```

### CommitEvent Table (History log)
```python
class CommitEvent(Base):
    __tablename__ = 'commit_events'
    
    id: int
    pet_state_id: int  # Foreign key
    
    commit_hash: str
    commit_message: str
    author_name: str
    author_email: str
    timestamp: datetime
    
    lines_added: int
    lines_deleted: int
    files_changed: int
    
    quality_score: float  # Individual commit quality
    mood_impact: str  # What mood change this caused
```

### StoryMemory Table (Cache generated stories)
```python
class StoryMemory(Base):
    __tablename__ = 'story_memories'
    
    id: int
    pet_state_id: int
    
    story_type: str  # forgotten_todo, old_code, author_tale, etc.
    story_text: str
    related_commit_hash: str
    generated_at: datetime
    times_shown: int = 0
```

## State Machine Logic

**File: `src/pet/states.py`**

### Enums
```python
from enum import Enum

class PetForm(Enum):
    EGG = "egg"              # 0-2 commits
    GHOST = "ghost"          # 3-5 commits (default path)
    ANGEL = "angel"          # 6+ commits, quality > 70
    DEMON = "demon"          # 6+ commits, quality < 30
    ZOMBIE = "zombie"        # 4+ reverts (sleepy, needs coffee)
    WRAITH = "wraith"        # 15+ commits (rare, ethereal)

class PetMood(Enum):
    JOYFUL = "joyful"        # Recent excellent commit
    HAPPY = "happy"          # Healthy regular activity
    CONTENT = "content"      # Baseline, all is well
    HUNGRY = "hungry"        # No commits in 24h
    TIRED = "tired"          # No commits in 3 days
    SLEEPING = "sleeping"    # No commits in 7 days (can be woken)
```

### PetStateMachine Class
```python
class PetStateMachine:
    def __init__(self, db_session, repo_path: str):
        """Initialize state machine with database session and repo path."""
        
    def feed(self, commit_data: dict) -> dict:
        """
        Process a new commit and update pet state.
        
        Returns:
        - mood_change: str
        - evolution_occurred: bool
        - friend_level_up: bool
        - message: str (encouraging message to show user)
        """
        
    def check_time_decay(self) -> dict:
        """
        Apply time-based mood decay (hunger, tiredness).
        Call this on every CLI invocation.
        
        Returns:
        - current_mood: PetMood
        - needs_attention: bool
        - message: str
        """
        
    def calculate_evolution(self) -> Optional[PetForm]:
        """
        Check if pet should evolve to new form.
        
        Returns new form if evolution occurs, None otherwise.
        """
        
    def interact(self, interaction_type: str) -> str:
        """
        Handle user interaction (pet, talk, play).
        Improves mood slightly, increases friendship.
        
        Returns: Friendly response message
        """
        
    def get_status(self) -> dict:
        """
        Get complete current state for display.
        
        Returns:
        - form: PetForm
        - mood: PetMood
        - stats: dict (all statistics)
        - next_evolution: dict (progress info)
        - friendship: dict (level and progress)
        """
```

## Evolution Rules (FAST PROGRESSION)

### Form Transitions
- **Egg → Ghost**: After 2-3 commits (quick start, celebratory)
- **Ghost → Angel**: 6-8 commits AND quality_score > 70 AND friend_level > 3
- **Ghost → Demon**: 6-8 commits AND quality_score < 30 (playful purple, not evil)
- **Ghost → Zombie**: 4-5 reverts (cute sleepy mint green, coffee lover)
- **Any → Wraith**: 15-20 commits AND friend_level = 10 (ultimate form, ethereal blue)

### Mood Transitions
- **Commit**: Improve mood by 1 level, reset hunger timer
- **High quality commit** (score > 80): +2 levels, +5 evolution points
- **Poor quality commit** (score < 30): No mood change, +1 evolution point
- **No activity 24h**: HAPPY → HUNGRY
- **No activity 3 days**: HUNGRY → TIRED
- **No activity 7 days**: TIRED → SLEEPING
- **Interaction**: SLEEPING → CONTENT (wake up!)

### Friendship Level
- Gained through: commits (+1 per commit), interactions (+0.5), time spent together
- Lost through: long absences (very slowly, -0.1 per week)
- Affects: evolution options, story richness, companion messages
- Max level: 10

## Database Operations

**File: `src/db/database.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

class Database:
    def __init__(self, repo_path: str):
        """Initialize database at {repo_path}/.gitgotchi.db"""
        
    def init_db(self):
        """Create all tables if they don't exist."""
        
    @contextmanager
    def session_scope(self) -> Session:
        """Provide transactional scope for database operations."""
        
    def get_or_create_pet(self, repo_path: str) -> PetState:
        """Get existing pet or create new one (egg form)."""
```

## Deliverables
1. ✅ `src/db/models.py` - All SQLAlchemy models
2. ✅ `src/db/database.py` - Database initialization and session management
3. ✅ `src/pet/states.py` - Complete state machine with all transitions
4. ✅ `src/pet/evolution.py` - Evolution calculation logic
5. ✅ Unit tests for state transitions

## Testing Requirements
- Mock commits with various quality scores
- Test all evolution paths (good dev → angel, chaos → demon, etc.)
- Test time decay (hunger → tired → sleeping progression)
- Test friendship level progression
- Test edge cases (empty repo, single commit, 1000+ commits)
- Test fast evolution (2-3 commits to ghost, 6-8 to angel/demon)
```

---

## 📋 Spec 2: Git History Analyzer

**File: `.kiro/specs/02_git_analyzer.md`**

```markdown
# Spec: Git History Analyzer

## Overview
Parse git repository history to extract data for feeding the companion and generating stories.

## Core Analyzer Class

**File: `src/seance/git_analyzer.py`**

```python
from git import Repo
from datetime import datetime
from typing import Optional, List, Dict

class GitAnalyzer:
    def __init__(self, repo_path: str):
        """Initialize with GitPython Repo object."""
        self.repo = Repo(repo_path)
        
    def get_latest_commit(self) -> Optional[Dict]:
        """
        Get the most recent commit.
        
        Returns None if repo has no commits.
        Returns dict with commit data structure (see below).
        """
        
    def analyze_commit(self, commit_hash: str) -> Dict:
        """
        Deep analysis of a specific commit.
        
        Returns:
        - hash: str
        - message: str
        - author_name: str
        - author_email: str
        - timestamp: datetime
        - files_changed: List[str]
        - lines_added: int
        - lines_deleted: int
        - is_merge: bool
        - quality_score: float (0-100)
        - notable_patterns: List[str]  # For story generation
        """
        
    def get_commit_history(self, limit: int = 100) -> List[Dict]:
        """Get recent commits for analysis."""
        
    def get_repository_stats(self) -> Dict:
        """
        Overall repository statistics.
        
        Returns:
        - total_commits: int
        - total_contributors: int
        - age_in_days: int
        - most_active_author: str
        - busiest_files: List[str]
        - language_breakdown: Dict[str, int]  # Estimated
        """
        
    def find_interesting_moments(self) -> List[Dict]:
        """
        Find moments worth telling stories about.
        
        Returns list of:
        - type: str (forgotten_todo, big_deletion, author_debut, etc.)
        - commit_hash: str
        - context: dict (relevant data for story generation)
        """
```

## Code Quality Scoring

**File: `src/seance/quality.py`**

```python
def calculate_commit_quality(commit_data: Dict) -> float:
    """
    Calculate quality score 0-100 for a commit.
    
    Scoring factors:
    
    Positive (add points):
    - +15: Descriptive message (50+ chars with context)
    - +10: Follows conventional commits (feat:, fix:, docs:, etc.)
    - +10: Includes test files
    - +5: Reasonable size (10-200 lines changed)
    - +5: Touches < 5 files (focused change)
    
    Negative (subtract points):
    - -20: Vague message (< 10 chars like "fix", "update", "wip")
    - -15: Huge commit (> 500 lines in one go)
    - -10: Merge commit with conflicts
    - -10: Only whitespace/formatting changes
    - -5: Commits generated files (dist/, build/, etc.)
    
    Base score: 50
    Final score: clamped to 0-100
    """
```

## Pattern Detection for Stories

**File: `src/seance/patterns.py`**

```python
def find_forgotten_todos(repo: Repo) -> List[Dict]:
    """
    Scan codebase for TODO comments and check their age via git blame.
    
    Returns list of:
    - file_path: str
    - line_number: int
    - todo_text: str
    - author: str
    - age_in_days: int
    - last_modified: datetime
    """

def find_code_resurrections(repo: Repo) -> List[Dict]:
    """
    Find code that was deleted and then re-added.
    
    Returns:
    - function_name: str
    - deleted_in: str (commit hash)
    - restored_in: str (commit hash)
    - time_between: int (days)
    """

def find_author_stories(repo: Repo) -> List[Dict]:
    """
    Find interesting author-related patterns.
    
    Returns:
    - first_timer_commits: List (first commit by each author)
    - prolific_authors: List (top contributors)
    - late_night_commits: List (commits after midnight)
    """

def find_major_changes(repo: Repo) -> List[Dict]:
    """
    Find significant code events.
    
    Returns:
    - big_deletions: List (> 100 lines deleted)
    - refactors: List (major file renames/restructures)
    - dependency_changes: List (package.json, requirements.txt changes)
    """
```

## Integration with Pet State

```python
def process_commit_for_pet(commit_data: Dict) -> Dict:
    """
    Transform git commit data into pet feeding data.
    
    Returns:
    - quality_score: float
    - mood_impact: str (joyful, happy, content, none)
    - evolution_points: int
    - story_triggers: List[str] (pattern types found)
    """
```

## Error Handling

Handle these cases gracefully:
- Empty repository (no commits yet)
- Corrupted git history
- Very large repositories (> 10k commits)
- Permission errors accessing .git directory
- Detached HEAD state
- Shallow clones (limited history)

All errors should return friendly messages via Rich console, never crash.

## Deliverables
1. ✅ `src/seance/git_analyzer.py` - Main analyzer class
2. ✅ `src/seance/quality.py` - Quality scoring logic
3. ✅ `src/seance/patterns.py` - Pattern detection for stories
4. ✅ Integration tests with real git repositories
```

---

## 📋 Spec 3: Terminal UI & Sprites

**File: `.kiro/specs/03_terminal_ui.md`**

```markdown
# Spec: Terminal UI & Pixel Sprites

## Overview
Create a cozy, Stardew Valley-inspired terminal interface using Rich library.

## UI Architecture

**File: `src/pet/renderer.py`**

```python
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.progress import Progress
from typing import Dict

class PetRenderer:
    def __init__(self):
        self.console = Console()
        
    def render_companion(self, state: Dict) -> Panel:
        """
        Render the main companion display.
        
        Returns Panel with:
        - Animated sprite (center)
        - Mood indicator
        - Current activity/message
        """
        
    def render_stats(self, state: Dict) -> Table:
        """
        Render statistics sidebar.
        
        Shows:
        - Friend Level: ❤️❤️❤️❤️❤️ (5/10)
        - Total Commits: 147
        - Form: 👻 Ghost
        - Mood: ✨ Joyful
        - Last Commit: 2 hours ago
        """
        
    def render_evolution_progress(self, state: Dict) -> Progress:
        """
        Show progress to next evolution.
        
        Use Rich Progress with custom bar:
        - Soft colors (lavender, mint, gold)
        - Sparkle emoji as progress indicator
        - "Next form: Angel 👼 (5/8 commits)"
        """
        
    def render_full_dashboard(self, state: Dict) -> Layout:
        """
        Complete dashboard layout:
        
        ┌─────────────────────────────────────────┐
        │         ✨ GitGotchi - Spirit ✨        │
        ├───────────────────┬─────────────────────┤
        │                   │  Friend Level: ❤️❤️❤️  │
        │      👻           │  Total Commits: 5    │
        │   (animated)      │  Form: Ghost         │
        │                   │  Mood: Happy         │
        │  "Great commit!"  │  Last Fed: 1hr ago   │
        ├───────────────────┴─────────────────────┤
        │ Evolution: ▰▰▰▰▰▱▱▱ 5/8 → Angel 👼      │
        └─────────────────────────────────────────┘
        """
```

## Sprite System

**File: `src/pet/animations.py`**

### Sprite Format
Use Unicode box-drawing and block characters for pixel art:
```
▀▄ █ ░▒▓ ▗▖▘▝
```

### Sprite Definitions

Each form has 3 mood variants + idle animation frames:

```python
SPRITES = {
    "egg": {
        "default": [
            # Frame 1
            """
              ▄▄▄▄
             █░░░░█
            █░░◉░░█
            █░░░░░█
             █████
            """,
            # Frame 2 (slightly different for breathing effect)
            """
              ▄▄▄▄
             █▒▒▒▒█
            █▒▒◉▒▒█
            █▒▒▒▒▒█
             █████
            """
        ]
    },
    
    "ghost": {
        "joyful": """
            ▄▄▄▄▄
           █ ◉ ◉ █
          █  ▼▼▼  █  ✨
          █       █
           █▀█▀█▀
        """,
        
        "happy": """
            ▄▄▄▄▄
           █ ◉ ◉ █
          █   ▼   █
          █       █
           █▀█▀█▀
        """,
        
        "content": """
            ▄▄▄▄▄
           █ ◉ ◉ █
          █   ─   █
          █       █
           █▀█▀█▀
        """,
        
        "hungry": """
            ▄▄▄▄▄
           █ ◉ ◉ █
          █   ~   █  🍂
          █       █
           █▀█▀█▀
        """,
        
        "sleeping": """
            ▄▄▄▄▄
           █ ─ ─ █
          █   ~   █  💤
          █       █
           █▀█▀█▀
        """
    },
    
    "angel": {
        "happy": """
           ✨ ✨ ✨
            ▄▄▄▄▄
           █ ◉ ◉ █
          █   ▼   █  👼
          █   💛  █
           █▀█▀█▀
        """
    },
    
    "demon": {
        "happy": """
           👿 ▄▄▄▄▄ 👿
           █ ◉ ◉ █
          █   ▼   █  💜
          █       █
           █▀█▀█▀
        """
    },
    
    "zombie": {
        "tired": """
            ▄▄▄▄▄
           █ ✕ ✕ █
          █   ~   █  ☕
          █ zzz   █
           █▀█▀█▀
        """
    },
    
    "wraith": {
        "content": """
         ✨  ▄▄▄▄▄  ✨
         🌙 █ ◉ ◉ █ 🌙
          █   ▼   █
          █  ~~~  █
           █▀█▀█▀
        """
    }
}
```

### Animation Engine
```python
class SpriteAnimator:
    def __init__(self, fps: int = 2):
        """Initialize animator with frame rate."""
        
    def get_frame(self, form: str, mood: str, frame_idx: int) -> str:
        """Get specific animation frame."""
        
    def animate_idle(self, form: str, mood: str) -> Generator[str]:
        """
        Generator that yields frames for idle animation.
        Yields frames forever, cycling through variants.
        """
```

## Color Scheme (Rich Console Styles)

```python
COLORS = {
    "background": "#2D1B2E",       # Deep purple
    "panel_border": "#8B7D8B",     # Soft lavender
    "text_primary": "#F0E6F0",     # Soft white
    "text_secondary": "#C8B8C8",   # Muted lavender
    
    # Mood colors
    "joyful": "#FFD700",           # Gold
    "happy": "#87CEEB",            # Sky blue
    "content": "#98D8C8",          # Mint
    "hungry": "#FFB6C1",           # Light pink
    "tired": "#B19CD9",            # Lavender
    
    # Form colors
    "egg": "#F0E68C",              # Khaki
    "ghost": "#E6E6FA",            # Lavender
    "angel": "#FFE4B5",            # Moccasin
    "demon": "#DDA0DD",            # Plum
    "zombie": "#98FB98",           # Pale green
    "wraith": "#B0C4DE",           # Light steel blue
}
```

## Interactive Commands

**File: `src/cli.py`**

```python
import click
from rich.console import Console

@click.group()
def cli():
    """GitGotchi - Your friendly dev companion 👻"""
    pass

@cli.command()
def status():
    """Show your companion's current status."""
    # Render full dashboard
    
@cli.command()
@click.argument('name')
def name(name: str):
    """Give your companion a name."""
    # Update pet_name in database
    
@cli.command()
def pet():
    """Pet your companion (boosts mood slightly)."""
    # Call state_machine.interact("pet")
    
@cli.command()
def story():
    """Hear a story about your code's history."""
    # Generate and display story
    
@cli.command()
def feed():
    """Manually check for new commits and feed."""
    # Analyze latest commits, update state
    
@cli.command()
def evolve():
    """Check evolution progress and requirements."""
    # Show detailed evolution requirements
```

## Deliverables
1. ✅ `src/pet/renderer.py` - Rich UI rendering
2. ✅ `src/pet/animations.py` - Sprite definitions and animator
3. ✅ `src/cli.py` - Click-based CLI interface
4. ✅ `assets/sprites/` - All sprite files (for documentation)
5. ✅ Color scheme configuration
```

---

## 📋 Spec 4: Story Generator

**File: `.kiro/specs/04_story_generator.md`**

```markdown
# Spec: Story Generator (LLM Integration)

## Overview
Generate warm, friendly stories about code history using Claude AI.

## Story Generator Class

**File: `src/seance/story_generator.py`**

```python
from anthropic import Anthropic
from typing import Dict, List, Optional
import random

class StoryGenerator:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        
    def generate_story(
        self, 
        story_type: str, 
        context: Dict,
        pet_form: str
    ) -> str:
        """
        Generate a story using Claude.
        
        Args:
        - story_type: Type of story (see STORY_TYPES below)
        - context: Relevant git data from patterns.py
        - pet_form: Current companion form (affects narrative voice)
        
        Returns: Friendly story text (2-4 paragraphs)
        """
        
    def get_daily_message(self, state: Dict) -> str:
        """
        Get a warm daily message based on current state.
        
        Examples:
        - "Good morning! Ready to write some code together? ✨"
        - "You've been working hard! Maybe time for a break? 🍂"
        - "I noticed you fixed that bug from last week. Nice work! 💛"
        """
        
    def get_evolution_message(self, old_form: str, new_form: str) -> str:
        """
        Special message for evolution events.
        
        Should be celebratory and encouraging.
        """
```

## Story Types & Templates

### 1. Forgotten TODO Story
```
Context needed:
- todo_text
- file_path
- age_in_days
- original_author

Tone: Gentle, slightly wistful

Example output:
"I found something interesting while exploring your code! 
There's a little note in auth.py that's been waiting for 
about 3 months now. It says 'TODO: add rate limiting'. 
I wonder what adventures that task has been dreaming of? 
Maybe today's the day it finally gets its moment! 🌟"
```

### 2. Code Resurrection Story
```
Context needed:
- function_name
- deleted_date
- restored_date
- time_between

Tone: Magical, like a phoenix

Example output:
"Something magical happened in your repository! The 
'calculateDiscount' function took a little vacation 
back in March, but guess what? It came back last week, 
ready for new adventures! Sometimes code needs a break 
before it can shine again. ✨"
```

### 3. First Commit Story
```
Context needed:
- author_name
- commit_date
- files_created
- message

Tone: Warm welcome, celebratory

Example output:
"A new friend joined your project today! Sarah made 
their first commit, bringing along some lovely new 
components. Every project starts with that first step, 
and this one looks like the beginning of something 
wonderful. Welcome to the team, Sarah! 🎉"
```

### 4. Late Night Coding Story
```
Context needed:
- commit_time (e.g., "2:47 AM")
- author
- what_changed

Tone: Cozy, understanding

Example output:
"I see you were up late last night! At 2:47 AM, you 
were working on the dashboard redesign. The stars were 
out, and so were you, bringing your ideas to life. 
I hope you got some rest afterward! Maybe add some 
comments so future-you remembers what midnight-you 
was thinking? 🌙"
```

### 5. Milestone Story
```
Context needed:
- milestone_type (10th commit, 1 month, etc.)
- relevant_stats

Tone: Celebratory, proud

Example output:
"Congratulations! This is your 10th commit together! 
From that first 'Initial commit' to now, we've written 
847 lines of code, fixed bugs, and built 
something really special. Here's to many more! 🎉✨"
```

## Prompt Engineering

### System Prompt Template
```python
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
```

### Story Generation Prompt
```python
def build_story_prompt(story_type: str, context: Dict) -> str:
    """Build prompt for Claude based on story type and context."""
    
    prompts = {
        "forgotten_todo": f"""
Tell a gentle story about a TODO comment that's been waiting in the code.

Details:
- The TODO says: "{context['todo_text']}"
- It's in: {context['file_path']}
- It's been there for: {context['age_in_days']} days
- Written by: {context['author']}

Make it feel like the TODO is an old friend patiently waiting, 
not a source of guilt. End with gentle encouragement to maybe 
revisit it someday.
        """,
        
        # ... more prompts for each story type
    }
    
    return prompts[story_type]
```

## Fallback System (Offline Mode)

**File: `src/seance/story_templates.py`**

```python
# Pre-written story templates for when API is unavailable
FALLBACK_STORIES = {
    "morning_greeting": [
        "Good morning! The code is waiting, and so am I! ✨",
        "A new day, a fresh start! What shall we build today? 🌅",
        "Hello friend! I've been keeping your code company. 💛"
    ],
    
    "commit_celebration": [
        "Another great commit! Your project is growing beautifully! 🌱",
        "Nice work! I felt that commit all the way from here! ✨",
        "You're on a roll! Keep up the wonderful work! 🎉"
    ],
    
    "encouragement": [
        "Every line of code is a step forward. You're doing great! 💛",
        "Progress isn't always visible, but I see how hard you work! ✨",
        "Even small commits make a difference. Keep going! 🌟"
    ]
}

def get_fallback_story(category: str) -> str:
    """Return a random pre-written story when API unavailable."""
    return random.choice(FALLBACK_STORIES.get(category, FALLBACK_STORIES["encouragement"]))
```

## Rate Limiting & Caching

```python
class StoryCacheManager:
    def __init__(self, db_session):
        self.db = db_session
        
    def get_cached_story(self, context_hash: str) -> Optional[str]:
        """Check if we've generated this story before."""
        
    def cache_story(self, context_hash: str, story: str):
        """Save generated story to avoid regenerating."""
        
    def should_generate_new_story(self, last_story_time: datetime) -> bool:
        """
        Rate limiting: Don't spam the API.
        Only generate new stories every 4 hours max.
        """
```

## Deliverables
1. ✅ `src/seance/story_generator.py` - Main generator with Claude integration
2. ✅ `src/seance/story_templates.py` - Fallback stories for offline mode
3. ✅ Story caching system in database
4. ✅ Rate limiting logic
5. ✅ Error handling for API failures
```

---

## 📋 Spec 5: Git Hooks Integration

**File: `.kiro/specs/05_git_hooks.md`**

```markdown
# Spec: Git Hooks Integration

## Overview
Automatically feed companion when commits happen using git hooks.

## Hook Installer

**File: `src/hooks/installer.py`**

```python
import os
import stat
from pathlib import Path

class GitHookInstaller:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.hooks_dir = self.repo_path / ".git" / "hooks"
        
    def install_hooks(self) -> bool:
        """
        Install post-commit and post-merge hooks.
        
        Returns True if successful, False otherwise.
        """
        
    def uninstall_hooks(self) -> bool:
        """Remove GitGotchi hooks."""
        
    def check_hooks_installed(self) -> Dict[str, bool]:
        """
        Check which hooks are currently installed.
        
        Returns:
        - post_commit: bool
        - post_merge: bool
        """
```

## Post-Commit Hook

**File: `.git/hooks/post-commit`** (generated)

```bash
#!/bin/bash
# GitGotchi post-commit hook
# This file is automatically generated - do not edit manually

# Activate virtual environment if it exists
if [ -d "venv/bin" ]; then
    source venv/bin/activate
fi

# Run the feed command silently in background
python -m gitgotchi feed --silent &

exit 0
```

**File: `src/hooks/post_commit.py`**

```python
def handle_post_commit(repo_path: str, silent: bool = False):
    """
    Handler called by post-commit hook.
    
    Tasks:
    1. Analyze the latest commit
    2. Calculate quality score
    3. Feed the companion (update state)
    4. Check for evolution
    5. Optionally show quick message (if not silent)
    
    Must be FAST (< 1 second) to not slow down git workflow.
    """
    
    try:
        # Initialize components
        analyzer = GitAnalyzer(repo_path)
        db = Database(repo_path)
        state_machine = PetStateMachine(db.session, repo_path)
        
        # Get latest commit
        commit = analyzer.get_latest_commit()
        
        # Process commit
        result = state_machine.feed(commit)
        
        # Show feedback if not silent
        if not silent and result['evolution_occurred']:
            console.print(f"✨ {result['message']} ✨")
            
    except Exception as e:
        # Log error but don't interrupt git workflow
        with open(f"{repo_path}/.gitgotchi.log", "a") as f:
            f.write(f"{datetime.now()}: Error in post-commit: {e}\n")
```

## Post-Merge Hook

**File: `.git/hooks/post-merge`** (generated)

```bash
#!/bin/bash
# GitGotchi post-merge hook

if [ -d "venv/bin" ]; then
    source venv/bin/activate
fi

# Check if merge had conflicts
if git ls-files -u | grep -q '^'; then
    python -m gitgotchi merge --conflicts &
else
    python -m gitgotchi merge --success &
fi

exit 0
```

**File: `src/hooks/post_merge.py`**

```python
def handle_post_merge(repo_path: str, had_conflicts: bool):
    """
    Handler for merge events.
    
    If merge had conflicts:
    - Companion becomes "tired" (merge conflicts are exhausting!)
    - Give encouraging message about resolving conflicts
    
    If merge was clean:
    - Celebrate successful collaboration
    - Boost mood
    """
```

## CLI Integration

Add to `src/cli.py`:

```python
@cli.command()
def install():
    """Install git hooks for automatic feeding."""
    installer = GitHookInstaller(os.getcwd())
    
    if installer.install_hooks():
        console.print("✨ Git hooks installed! Your companion will be fed automatically on commits.")
    else:
        console.print("❌ Failed to install hooks. Make sure you're in a git repository.")

@cli.command()
def uninstall():
    """Remove git hooks."""
    installer = GitHookInstaller(os.getcwd())
    
    if installer.uninstall_hooks():
        console.print("👋 Git hooks removed. You can still feed manually with 'gitgotchi feed'.")

@cli.command()
@click.option('--silent', is_flag=True)
def feed(silent: bool):
    """Check for new commits and feed companion."""
    handle_post_commit(os.getcwd(), silent=silent)
```

## Safety & Performance

### Performance Requirements
- Hook execution must complete in < 1 second
- Run in background to not block git operations
- Batch multiple rapid commits (debounce)
- Cache git analysis results

### Safety Checks
```python
def safe_hook_execution(func):
    """Decorator to ensure hooks never break git workflow."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log error but don't propagate
            log_error(e)
            return None
    return wrapper
```

## Deliverables
1. ✅ `src/hooks/installer.py` - Hook installation logic
2. ✅ `src/hooks/post_commit.py` - Commit handler
3. ✅ `src/hooks/post_merge.py` - Merge handler
4. ✅ Hook templates (bash scripts)
5. ✅ CLI commands for install/uninstall
6. ✅ Performance optimizations (caching, async)
```

---

## 🚀 Implementation Order

### Week 1: Core Foundation
1. ✅ Set up project structure
2. ✅ Implement database models (`01_pet_state_system.md`)
3. ✅ Build state machine with all transitions (FAST evolution every 2-3 commits)
4. ✅ Create git analyzer (`02_git_analyzer.md`)
5. ✅ Write unit tests for core logic

### Week 2: User Interface
1. ✅ Design and implement sprites (`03_terminal_ui.md`)
2. ✅ Build Rich-based terminal UI
3. ✅ Create CLI commands
4. ✅ Add animation system
5. ✅ Test UI with mock data

### Week 3: Stories & Polish
1. ✅ Implement story generator (`04_story_generator.md`)
2. ✅ Install git hooks (`05_git_hooks.md`)
3. ✅ Add fallback stories for offline mode
4. ✅ Create demo video
5. ✅ Write comprehensive README

---

## 📦 Additional Files Needed

### requirements.txt
```
rich==13.7.0
gitpython==3.1.40
anthropic==0.34.0
sqlalchemy==2.0.23
click==8.1.7
python-dotenv==1.0.0
pytest==7.4.3
pytest-cov==4.1.0
```

### .env.example
```
ANTHROPIC_API_KEY=your_api_key_here
GITGOTCHI_DB_PATH=.gitgotchi.db
LOG_LEVEL=INFO
```

### .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
venv/
.env

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/

# Testing
.pytest_cache/
.coverage
htmlcov/

# DO NOT IGNORE .kiro/
# We need to commit this for the hackathon!
```

### README.md
```markdown
# 🎃 GitGotchi - Your Friendly Dev Companion 👻

A Stardew Valley-inspired terminal companion that lives in your git repository!

## ✨ Features
- Adorable pixel art companion that evolves based on your coding habits
- Warm, encouraging stories about your code history
- Automatic feeding through git hooks
- Friendship system inspired by Stardew Valley
- Cozy terminal UI with sparkles and hearts
- Fast evolution - see changes every 2-3 commits!

## 🚀 Quick Start
```bash
pip install -r requirements.txt
python -m gitgotchi install  # Install git hooks
python -m gitgotchi status   # Meet your companion!
```

## 🎮 Commands
- `gitgotchi status` - See your companion
- `gitgotchi pet` - Give them affection
- `gitgotchi story` - Hear a code story
- `gitgotchi evolve` - Check evolution progress

## 🌟 Evolution Forms (Fast Track!)
- 🥚 Egg (0-2 commits)
- 👻 Ghost (3-5 commits)
- 👼 Angel (6-8 commits, high quality)
- 😈 Demon (6-8 commits, chaotic)
- 🧟 Zombie (4-5 reverts, needs coffee)
- 🌙 Wraith (15-20 commits, ultimate form)

Built with ❤️ for Kiroween Hackathon 2024
```

---

## 🎬 Demo Video Script

**3-Minute Structure:**

**0:00-0:30 - The Hook**
- Cozy terminal opens, soft music
- "Meet your new dev companion..."
- Show egg hatching into friendly ghost after just 2 commits
- Tagline: "GitGotchi - Code with a friend"

**0:30-1:30 - Core Features**
- Make a commit → companion gets fed, happy animation
- Show dashboard with stats and friendship hearts
- Pet the companion → cute response
- Ask for a story → warm tale about code history
- Make 2 more commits → ghost evolves to angel! ✨

**1:30-2:15 - Kiro Showcase**
- Quick cuts showing:
  - Vibe coding: "Built the state machine by chatting with Kiro"
  - Specs: Show `.kiro/specs/` directory with 5 organized specs
  - Hooks: Git hook auto-installing
  - MCP: Custom git analysis tools
  - Steering: "Kept the cozy Stardew Valley vibe consistent"

**2:15-2:45 - Evolution Montage**
- Fast-forward showing rapid evolution
- Ghost → Angel (just 3 commits, sparkles!)
- Ghost → Demon (different path, playful horns)
- Ghost → Zombie (after reverts, sleepy, coffee mug)
- Ultimate form: Wraith (ethereal and glowing)

**2:45-3:00 - Call to Action**
- "Every commit is better with a friend"
- "See your companion grow in just minutes!"
- Show GitHub repo link
- "Made with Kiro - try it yourself!"
- Final shot: Companion waving goodbye

---

## 🎯 Kiro Usage Documentation

**For Judges - How Kiro Was Used:**

### 1. Vibe Coding
- **Natural conversation** to design the state machine logic
- Asked Kiro: "How should friendship levels work like in Stardew Valley?"
- Iterated on sprite designs through chat
- Kiro suggested using Rich library for better terminal UI
- Discussed fast evolution pacing (2-3 commits vs 10-50)

### 2. Spec-Driven Development
- Created 5 comprehensive specs in `.kiro/specs/`
- Each spec defined clear deliverables and requirements
- Kiro implemented each spec systematically
- Specs kept project organized and trackable
- Evolution rules clearly documented in spec 01

### 3. Agent Hooks
- `.kiro/hooks/pre_commit_check.sh` - validates sprite file formats
- Auto-runs code formatting before commits
- Improved workflow consistency

### 4. Steering Documents
- `.kiro/steering/project_voice.md` maintained consistent:
  - Stardew Valley aesthetic (not scary!)
  - Friendly, warm tone in all generated text
  - Code style preferences (type hints, docstrings)
  - Error message formatting (always encouraging)

### 5. MCP (Model Context Protocol)
- Custom MCP server for deep git analysis
- Tool: `analyze_repository_patterns` - finds interesting code moments
- Tool: `calculate_code_quality` - scores commits
- Tool: `detect_evolution_triggers` - determines when pet should evolve
- Enabled sophisticated git forensics beyond basic GitPython

### Most Impressive Generation
Kiro generated the entire state machine with 6 forms, 6 moods, and all transition logic in one shot after reading the spec. It included proper SQLAlchemy models, transition validation, fast evolution pacing (2-3 commits to ghost, 6-8 to advanced forms), and even edge case handling for repos with no commits.

---

## 🏆 Category: Frankenstein

**Stitching Together:**
- Git (GitPython) - repository analysis
- LLM (Anthropic Claude) - story generation
- Terminal UI (Rich) - visual interface
- SQLite (SQLAlchemy) - persistent state
- Bash hooks - git integration
- Click - CLI framework

**The Chimera:** A pixel art companion that lives at the intersection of git history, AI storytelling, and cozy game design. Code analysis meets emotional support!

---

## ✅ Final Checklist

Before submission:
- [ ] All 5 specs in `.kiro/specs/` committed
- [ ] Steering doc in `.kiro/steering/` committed
- [ ] DO NOT add `.kiro/` to `.gitignore`
- [ ] README with Kiro usage explanation
- [ ] Demo video uploaded (YouTube/Vimeo)
- [ ] Application works offline (fallback stories)
- [ ] Git hooks auto-install successfully
- [ ] All sprites render correctly in terminal
- [ ] Database initializes on first run
- [ ] Tested on fresh clone of repo
- [ ] Fast evolution verified (2-3 commits to ghost, 6-8 to angel/demon)
- [ ] Evolution progress shown clearly in UI

---

## 🚀 Getting Started with Kiro

1. Save this entire document as `GITGOTCHI_COMPLETE_SPEC.md`
2. Create your project directory: `mkdir gitgotchi && cd gitgotchi`
3. Initialize git: `git init`
4. Open Kiro in this directory
5. Give Kiro this prompt:

```
Build GitGotchi following the 5 specs in this document. 

Start with spec 01 (Pet State System with FAST evolution every 2-3 commits), 
then 02 (Git Analyzer), 03 (Terminal UI), 04 (Story Generator), and 
finally 05 (Git Hooks). 

Follow the steering document in .kiro/steering/project_voice.md for 
code style and the cozy Stardew Valley theme. 

Make evolution happen quickly - egg to ghost in 2-3 commits, 
ghost to angel/demon in 6-8 commits total. Show progress clearly in the UI.

Let's build something magical! ✨
```

Then let Kiro work its magic! 🎃👻