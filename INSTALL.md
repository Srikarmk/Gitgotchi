# GitGotchi Installation Guide

## Install

```bash
pip install gitgotchi
gitgotchi --help
```

Or, to keep it isolated from your other Python packages:

```bash
pipx install gitgotchi
```

## Setup

1. **Go to any git repository**:

```bash
cd your-project
```

2. **Install the hook and meet your companion**:

```bash
gitgotchi install
gitgotchi status
```

3. **Make commits and watch your companion grow!**

```bash
git add .
git commit -m "feat: add cool feature"
gitgotchi status  # Your companion just got fed! 🌟
```

4. **Optional: AI stories.** Get an API key from the [Anthropic Console](https://console.anthropic.com)
   and set it:

```bash
export ANTHROPIC_API_KEY='your-key-here'
# or
echo "ANTHROPIC_API_KEY=your-key-here" >> .env
```

## Requirements

- Python 3.10 or higher
- Git installed and configured
- A git repository (run `git init` if needed)

## Troubleshooting

### "Command not found: gitgotchi"

Make sure the package is installed and your Python scripts directory is on your PATH:

```bash
pip show gitgotchi
```

`pipx install gitgotchi` takes care of PATH for you.

### "No git repository found"

GitGotchi lives inside a git repository. Initialize one first:

```bash
git init
```

### My companion stopped eating after I recreated my virtualenv

The hook remembers which Python it was installed with. Re-run `gitgotchi install` from the new
environment and it will update the hook in place.

### Upgrading from 0.1.x

0.1.x installed its code as a package named `src`, which broke the hook in projects that have
their own `src/` package. After upgrading, run `gitgotchi install` once in each repository to
replace the old hook. Your companion's state is kept.

## Development

```bash
git clone https://github.com/Srikarmk/Gitgotchi.git
cd Gitgotchi
pip install -e ".[dev]"
pytest
```

### Building

```bash
python -m build
# dist/gitgotchi-<version>.tar.gz
# dist/gitgotchi-<version>-py3-none-any.whl
```

### Testing the build in a clean environment

```bash
python -m venv /tmp/gg-test
source /tmp/gg-test/bin/activate  # On Windows: \tmp\gg-test\Scripts\activate
pip install dist/gitgotchi-*.whl
gitgotchi version
deactivate
```

### Releasing

Bump `__version__` in `src/gitgotchi/__init__.py`, add a CHANGELOG entry, then tag:

```bash
git tag v0.2.0
git push origin v0.2.0
```

The Publish workflow builds the package and uploads it to PyPI.

## Uninstallation

```bash
gitgotchi uninstall   # in each repo
pip uninstall gitgotchi
```

Enjoy your new companion! 👻✨
