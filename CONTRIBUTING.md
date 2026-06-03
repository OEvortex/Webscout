# Contributing to Webscout

First off, thanks for taking the time to contribute! 🎉

Webscout is an all-in-one Python toolkit, and every contribution helps make it better.

## Code of Conduct

By participating in this project, you agree to be respectful and constructive in all interactions.

## How to Contribute

### 🐛 Reporting Bugs

1. **Check existing issues** — see if it's already reported
2. **Open a bug report** — use the issue template and include:
   - Python version and OS
   - Steps to reproduce
   - Expected vs actual behavior
   - Full error output

### 💡 Suggesting Features

Open a feature request issue with:
- A clear description of what you want
- Why it's useful for Webscout
- Any implementation ideas you have

### 🔧 Pull Requests

1. **Fork the repo** and create your branch from `main`
2. **Run tests** before submitting: `pytest tests/` or `python -m pytest`
3. **Keep changes focused** — one feature/fix per PR
4. **Write clear commit messages**
5. **Update docs** if you change behavior
6. **Link the PR** to any related issue

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Webscout.git
cd Webscout

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Style Guidelines

- **Python**: Follow [PEP 8](https://peps.python.org/pep-0008/)
- **Imports**: Standard lib → third-party → local, grouped with blank lines
- **Type hints**: Use them for all public functions
- **Docstrings**: Google-style docstrings for all modules and functions

```python
def example_function(param1: str, param2: int) -> bool:
    \"\"\"Short description.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.
    \"\"\"
    return True
```

## Project Structure

```
webscout/
├── webscout/          # Main source
│   ├── ai/           # AI model integrations
│   ├── search/       # Search engine wrappers
│   ├── utils/        # Shared utilities
│   └── cli/          # Command-line interface
├── tests/            # Test suite
├── docs/             # Documentation
└── examples/         # Usage examples
```

## Need Help?

Open a discussion or ask in the issue tracker. We're here to help! 🚀
