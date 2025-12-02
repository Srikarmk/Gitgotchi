# GitGotchi Installation Guide

## Quick Install (Recommended)

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/gitgotchi.git
cd gitgotchi

# Install in development mode
pip install -e .

# Verify installation
gitgotchi --help
```

### From PyPI (When Published)

```bash
# Install from PyPI
pip install gitgotchi

# Verify installation
gitgotchi --help
```

## Setup

1. **Get your Anthropic API key** (optional, for story generation):
   - Visit [Anthropic Console](https://console.anthropic.com)
   - Sign up for free credits
   - Copy your API key

2. **Set environment variable**:

```bash
# Option 1: Export (temporary)
export ANTHROPIC_API_KEY='your-key-here'

# Option 2: Create .env file (recommended)
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

3. **Navigate to any git repository**:

```bash
cd your-project
```

4. **Install hooks and meet your companion**:

```bash
gitgotchi install
gitgotchi status
```

5. **Make commits and watch your companion grow!**

```bash
git add .
git commit -m "feat: add cool feature"
gitgotchi status  # Your companion just got fed! 🌟
```

## Requirements

- Python 3.10 or higher
- Git installed and configured
- A git repository (run `git init` if needed)

## Troubleshooting

### "Command not found: gitgotchi"

**Solution**: Make sure the package is installed and your PATH includes Python scripts:

```bash
# Check if installed
pip list | grep gitgotchi

# Reinstall if needed
pip install -e . --force-reinstall
```

### "No module named 'src'"

**Solution**: Install in development mode from the project root:

```bash
cd gitgotchi
pip install -e .
```

### "Not a git repository"

**Solution**: Initialize git first:

```bash
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

## Building from Source

To build the package for distribution:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# This creates:
# dist/gitgotchi-0.1.0.tar.gz (source)
# dist/gitgotchi-0.1.0-py3-none-any.whl (wheel)
```

## Testing the Build

```bash
# Create a test virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from local build
pip install dist/gitgotchi-0.1.0-py3-none-any.whl

# Test it works
gitgotchi status

# Clean up
deactivate
rm -rf test_env
```

## Uninstallation

```bash
# Remove git hooks first
gitgotchi uninstall

# Uninstall package
pip uninstall gitgotchi
```

## Next Steps

Once installed, check out:
- [README.md](README.md) - Full documentation
- [KIRO_USAGE.md](KIRO_USAGE.md) - How Kiro was used to build this
- [gitgotchi_spec.md](gitgotchi_spec.md) - Complete specification

Enjoy your new companion! 👻✨
