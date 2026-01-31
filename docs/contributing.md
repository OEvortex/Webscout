# Contributing to Webscout

> **Last updated:** 2026-01-24  
> **Type:** Developer Guide  
> **Status:** Active contributions welcome

## Welcome!

Thank you for considering contributing to Webscout. This guide will help you get started with development and ensure your contributions meet our quality standards.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Types of Contributions](#types-of-contributions)
- [Code Quality Standards](#code-quality-standards)
- [Testing Requirements](#testing-requirements)
- [Commit Standards](#commit-standards)
- [Pull Request Process](#pull-request-process)
- [Documentation Standards](#documentation-standards)

---

## Getting Started

### Prerequisites

- Python 3.8+
- Git
- A GitHub account

### Fork and Clone

```bash
# 1. Fork the repository on GitHub
# Visit: https://github.com/OEvortex/Webscout

# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/Webscout.git
cd Webscout

# 3. Add upstream remote
git remote add upstream https://github.com/OEvortex/Webscout.git

# 4. Verify remotes
git remote -v
# origin   YOUR-FORK (fetch/push)
# upstream ORIGINAL (fetch)
```

---

## Development Setup

### Using UV (Recommended)

```bash
# Install UV if not already installed
pip install uv

# Install with development dependencies
uv sync --extra dev --extra api

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Run type checker
uv run ty check .
```

### Using pip

```bash
# Create virtual environment
python -m venv venv

# Activate
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

# Install in development mode
pip install -e ".[dev,api]"

# Install linting and type checking tools
pip install ruff ty
```

### Verify Setup

```bash
# Check Python version
python --version

# Check Webscout import
python -c "import webscout; print(webscout.__version__)"

# Check tools
ruff --version
ty --version
```

---

## Types of Contributions

### 1. New Providers

See [Provider Development Guide](provider-development.md) for detailed instructions.

```python
# Example structure
class NewProvider(Provider):
    required_auth = False/True
    
    def __init__(self, ...):
        # Implementation
        pass
    
    def ask(self, prompt: str, **kwargs):
        # Implementation
        pass
    
    def chat(self, prompt: str, **kwargs):
        # Implementation
        pass
    
    def get_message(self, response):
        # Implementation
        pass
```

### 2. Bug Fixes

```bash
# Create issue branch
git checkout -b fix/issue-description

# Make changes
# ... edit files ...

# Test changes
uv run pytest tests/

# Commit
git commit -m "fix: brief description of fix"

# Push
git push origin fix/issue-description
```

### 3. Features

```bash
# Create feature branch
git checkout -b feature/feature-name

# Make changes
# ... implement feature ...

# Add tests
# ... create tests/test_feature.py ...

# Commit and push
git commit -m "feat: add new feature"
git push origin feature/feature-name
```

### 4. Documentation

```bash
# Create docs branch
git checkout -b docs/update-name

# Edit docs
# ... edit files in docs/ ...

# Verify markdown renders properly
# Commit and push
git commit -m "docs: update documentation"
git push origin docs/update-name
```

---

## Code Quality Standards

### Line Length

Maximum 100 characters (enforced by Ruff):

```python
# ✓ Good - under 100 characters
response = client.chat("Hello", max_tokens=100, temperature=0.7)

# ❌ Bad - over 100 characters
response = client.chat("Hello", max_tokens=100, temperature=0.7, TOP_P=0.9, presence_penalty=0)
# Should be split:
response = client.chat(
    "Hello",
    max_tokens=100,
    temperature=0.7,
    top_p=0.9,
    presence_penalty=0,
)
```

### Type Hints

All functions must have type hints:

```python
# ✓ Good - complete type hints
def chat(
    self,
    prompt: str,
    stream: bool = False,
    **kwargs: Any,
) -> Union[str, Generator[str, None, None]]:
    pass

# ❌ Bad - missing type hints
def chat(self, prompt, stream=False, **kwargs):
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def chat(
    self,
    prompt: str,
    stream: bool = False,
) -> str:
    """
    Send a prompt and get a response.
    
    Args:
        prompt (str): The user's prompt
        stream (bool): Whether to stream response. Defaults to False.
    
    Returns:
        str: The AI response
    
    Raises:
        ProviderException: If the request fails
    
    Example:
        >>> client = MyProvider(api_key="key")
        >>> response = client.chat("Hello")
        >>> print(response)
    """
    pass
```

### Imports

Keep imports organized:

```python
# Order: standard library, third-party, local
import json
from typing import Any, Dict, Optional

import requests
from curl_cffi.requests import Session

from webscout.AIbase import Provider
from webscout import exceptions
```

### Naming Conventions

```python
# Classes: PascalCase
class MyProvider:
    pass

# Functions/methods: snake_case
def get_response():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_TOKENS = 1000

# Private: _leading_underscore
def _internal_method():
    pass
```

---

## Testing Requirements

### Run All Tests

```bash
# Run full test suite
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/providers/test_groq.py

# Run specific test
uv run pytest tests/providers/test_groq.py::TestGROQ::test_chat
```

### Write Tests

Create `tests/providers/test_yourprovider.py`:

```python
import unittest
from unittest.mock import patch, MagicMock

from webscout.Provider.YourProvider import YourProvider


class TestYourProvider(unittest.TestCase):
    
    def setUp(self):
        """Setup test fixtures."""
        self.provider = YourProvider(api_key="test-key")
    
    @patch('webscout.Provider.YourProvider.Session.post')
    def test_chat_basic(self, mock_post):
        """Test basic chat functionality."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response
        
        response = self.provider.chat("Hello")
        self.assertEqual(response, "Test response")
    
    @patch('webscout.Provider.YourProvider.Session.post')
    def test_chat_streaming(self, mock_post):
        """Test streaming responses."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Chunk 1"}}]
        }
        mock_post.return_value = mock_response
        
        response = self.provider.chat("Hello", stream=True)
        chunks = list(response)
        self.assertTrue(len(chunks) > 0)
    
    def test_authentication_required(self):
        """Test that provider requires authentication."""
        self.assertTrue(self.provider.required_auth)


if __name__ == "__main__":
    unittest.main()
```

### Test Coverage

Aim for at least 80% coverage:

```bash
# Run tests with coverage
uv run pytest --cov=webscout tests/

# Generate coverage report
uv run pytest --cov=webscout --cov-report=html tests/
# Open htmlcov/index.html to view report
```

---

## Linting & Type Checking

### Ruff (Linting & Formatting)

```bash
# Check all files
uv run ruff check .

# Fix automatically fixable issues
uv run ruff check . --fix

# Check specific file
uv run ruff check webscout/Provider/MyProvider.py

# Format code
uv run ruff format .
```

### Type Checking with Ty

```bash
# Check all files
uv run ty check .

# Check specific file
uv run ty check webscout/Provider/MyProvider.py
```

### Quality Checklist

Before submitting a PR:

```bash
# 1. Run linter
uv run ruff check .

# 2. Fix linter issues
uv run ruff check . --fix

# 3. Run type checker
uv run ty check .

# 4. Run tests
uv run pytest

# 5. Check coverage
uv run pytest --cov=webscout tests/

# All should pass ✓
```

---

## Commit Standards

### Commit Message Format

Use conventional commits:

```
<type>: <description>

<body>

<footer>
```

### Types

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style (spacing, formatting)
- `refactor:` Code changes without feature/fix
- `perf:` Performance improvements
- `test:` Test changes
- `chore:` Maintenance tasks

### Examples

```bash
# Good commit messages
git commit -m "feat: add caching to provider responses"
git commit -m "fix: handle network timeout in GROQ provider"
git commit -m "docs: update getting started guide"
git commit -m "refactor: simplify chat method logic"

# Bad commit messages
git commit -m "Update stuff"
git commit -m "Fixed things"
git commit -m "Random changes"
```

### Write Descriptive Commits

```python
# If your change is more complex, provide context

git commit -m "feat: implement conversation history

This adds support for multi-turn conversations with automatic
context management. Conversation history is stored in memory
and cleared on provider reset.

Implements request #123"
```

---

## Pull Request Process

### Before You Start

1. **Create an issue** for major changes
2. **Check existing PRs** to avoid duplicates
3. **Sync with upstream** to avoid conflicts

```bash
# Update from upstream
git fetch upstream
git rebase upstream/main
```

### Submit Your PR

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature
   ```

2. **Create PR on GitHub:**
   - Base: `OEvortex/Webscout` main
   - Compare: `YOUR-USERNAME/Webscout` your-branch
   - Title: Brief description
   - Description: Details about changes

3. **PR Description Template:**
   ```markdown
   ## Description
   Brief explanation of what this PR does.
   
   ## Type of Change
   - [ ] New feature
   - [ ] Bug fix
   - [ ] Documentation
   - [ ] Provider implementation
   
   ## Related Issue
   Closes #123
   
   ## Testing
   Steps to verify the changes work correctly.
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] Linting passes
   - [ ] Type checking passes
   ```

### Review Process

- **Automated checks** must pass (CI/CD)
- **Code review** by maintainers
- **Changes may be requested** - respond promptly
- **Approval** from at least one maintainer
- **Merge** when ready

### Common Review Comments

| Comment | What to Do |
|---------|-----------|
| "Please add type hints" | Add type annotations to function |
| "Can you add a test?" | Create unit test for new code |
| "Ruff found issues" | Fix linting: `ruff check . --fix` |
| "Type checker failed" | Fix type hints for proper typing |
| "Update docs" | Document your new feature |

---

## Documentation Standards

### Markdown Files

Keep to these standards:

```markdown
# Heading 1 - File title (use only once per file)

> Context about the file
> Last updated: date
> Type: guide/reference

## Heading 2 - Major section

### Heading 3 - Subsection

#### Heading 4 - Sub-subsection

**Bold** for emphasis  
*Italic* for terms  
`code` for inline code

\`\`\`python
# Code blocks with language
code here
\`\`\`

- Bullet lists
- Are structured
- And easy to scan

| Table | Headers |
|-------|---------|
| are | useful |
| for | comparisons |

[Links](path/to/file.md) are relative paths
```

### Code Examples

Include runnable examples:

```python
# ✓ Good - complete, runnable example
from webscout import GROQ

client = GROQ(api_key="your-key")
response = client.chat("What is machine learning?")
print(response)

# ❌ Bad - incomplete example
client = GROQ(api_key="key")
response = client.chat("What is ML?")
```

### Cross-References

Use relative paths:

```markdown
# Instead of absolute paths
[Getting Started](../getting-started.md)
[API Reference](api-reference.md)
[Provider List](../Provider.md)

# Not: https://github.com/... (too specific)
```

---

## Architecture Guidelines

Follow the structure in [AGENTS.md](../AGENTS.md):

- Provider implementations go in `webscout/Provider/`
- Search engines go in `webscout/search/`
- Utilities go in `webscout/Extra/`
- Tests go in `tests/providers/`
- Documentation goes in `docs/`

---

## Getting Help

- **Questions:** [GitHub Discussions](https://github.com/OEvortex/Webscout/discussions)
- **Issues:** [GitHub Issues](https://github.com/OEvortex/Webscout/issues)
- **Chat:** [Telegram Group](https://t.me/OEvortexAI)
- **Documentation:** [docs/README.md](README.md)

---

## Summary

1. ✅ Fork and clone repository
2. ✅ Set up development environment with UV
3. ✅ Create a feature/fix branch
4. ✅ Make changes following code standards
5. ✅ Write/update tests
6. ✅ Ensure all checks pass:
   - `ruff check . --fix`
   - `ty check .`
   - `pytest`
7. ✅ Commit with conventional messages
8. ✅ Push and create PR
9. ✅ Respond to review comments
10. ✅ Celebrate your contribution! 🎉

Thank you for contributing to Webscout!
