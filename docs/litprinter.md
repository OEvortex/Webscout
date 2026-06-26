# LitPrinter: Advanced Terminal Output & Debugging Library
> Last updated: 2025-12-20
> Maintained by [OEvortex](https://github.com/OEvortex/litprinter)

**🔥 The Most Sophisticated Terminal Output & Debugging Library for Python**

**🎨 Rich Formatting • IceCream Debugging • Beautiful Panels • Syntax Highlighting • Enhanced Tracebacks**

## 📋 Overview

LitPrinter is a comprehensive terminal output library that combines the power of IceCream-style debugging with Rich-style formatting and UI components. It provides a sophisticated set of tools for creating beautiful, informative, and highly readable terminal applications and debug logs.

<details open>
<summary><b>🌟 Key Features</b></summary>

- **🍦 IceCream-Compatible Debugging**: Powerful `ic()` function for effortless variable inspection.
- **🖥️ Rich Console**: Advanced `Console` class with markup support, logging, and JSON highlighting.
- **🖼️ Beautiful Panels**: Professional bordered content areas with multiple styles, shadows, and alignment.
- **💥 Enhanced Tracebacks**: Syntax-highlighted, informative tracebacks with local variable inspection.
- **🎨 Sophisticated Styling**: Support for multiple themes (TokyoNight, Cyberpunk, Dracula, etc.) and custom styles.
- **📊 Layout Management**: `PanelGroup` for vertical, horizontal, and grid-based layouts.
- **🛠️ Highly Customizable**: Configure prefixes, output functions, and register custom formatters.

</details>

## 📑 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [IceCream Debugging (`ic`)](#-icecream-debugging-ic)
- [Rich Console (`Console`)](#-rich-console-console)
- [Panels & Layouts (`Panel`)](#-panels--layouts-panel)
- [Traceback Enhancement](#-traceback-enhancement)
- [Themes & Styles](#-themes--styles)
- [API Reference](#-api-reference)
- [License](#-license)

## 📦 Installation

Install LitPrinter using pip:

```bash
pip install litprinter
```

## 🚀 Quick Start

```python
from litprinter import ic, Console, Panel, TokyoNight

# 1. IceCream-style debugging
x = {"a": 1, "b": [1, 2, 3]}
ic(x)  # Output: ic| x: {'a': 1, 'b': [1, 2, 3]}

# 2. Rich-style console output
console = Console()
console.print("[bold cyan]Welcome to [magenta]LitPrinter[/magenta]![/bold cyan]")
console.rule("Section Header")

# 3. Beautiful Panels
print(Panel("This is a panel", title="Info", border_style="rounded"))
```

---

## 🍦 IceCream Debugging (`ic`)

LitPrinter provides a drop-in replacement for the popular `icecream` library with enhanced formatting capabilities.

### Basic Usage
```python
from litprinter import ic

def add(a, b):
    return a + b

ic(add(10, 20))
# Output: ic| test.py:4 in add() >>> add(10, 20): 30
```

### Configuration Options
```python
from litprinter import ic

# Global configuration
ic.configureOutput(
    prefix="DEBUG| ",
    includeContext=True,        # Show file, line, and function
    contextAbsPath=False,       # Use relative paths
    outputFunction=print,       # Custom output function
    argToStringFunction=str        # Custom argument formatter
)

# Per-call overrides
ic(x, includeContext=True, contextAbsPath=True)

# Enable/disable output
ic.disable()
ic.enable()

# Format without printing
formatted = ic.format(x, y)
print(formatted)
```

### Available Aliases
```python
from litprinter import lit, litprint, LIT
# All are aliases for the same ic functionality
```

---

## 🖥️ Rich Console (`Console`)

The `Console` class provides a comprehensive API for styled terminal output with Rich-like capabilities.

### Markup and Styling
```python
from litprinter import Console
console = Console()

# Rich-style markup
console.print("[red]Error:[/red] [bold]Something went wrong![/bold]")
console.print("Hex colors: [#ff5555]Custom Red[/#ff5555]")
console.print("Background: [on_blue]Blue text[/on_blue]")

# Multiple style combinations
console.print("[bold italic yellow]Warning:[/bold italic yellow] Low disk space")
```

### Logging with Context
```python
# Enhanced logging with timestamps and location
console.log("Application started", log_locals=True)
console.log("Processing user request", log_locals=False)

# Different log levels implicitly supported through styling
console.log("[red]Critical error occurred[/red]")
console.log("[yellow]Warning: deprecated API[/yellow]")
```

### JSON and Data Formatting
```python
# Pretty-print JSON with syntax highlighting
data = {
    "name": "LitPrinter",
    "version": "0.3.3",
    "features": ["debugging", "formatting", "tracebacks"],
    "active": True
}
console.print_json(data, indent=2)

# Custom highlighting options
console.print_json(data, highlight=True, skip_keys=False, ensure_ascii=False)
```

### Advanced Console Features
```python
console = Console()

# Horizontal rules with alignment and styling
console.rule("Section 1", characters="─", style="dim", align="center")
console.rule("Data Processing", characters="=", style="bold")

# Status with spinners (simple implementation)
with console.status("Processing data...", spinner="dots"):
    # Long-running operation
    process_large_dataset()

# Styled input prompts
name = console.input("[bold cyan]Enter your name: [/bold cyan]")
password = console.input("[bold yellow]Password: [/bold yellow]", password=True)

# Terminal control and capabilities
console.clear(home=True)        # Clear and move to home
console.clear_line()           # Clear current line
console.show_cursor(False)      # Hide cursor
console.bell()                 # Play bell sound
console.set_window_title("My Application")  # Set terminal title
```

### Output Capture and Export
```python
console = Console(record=True)

# Capture all output
with console.capture() as capture:
    console.print("[bold green]This will be captured[/bold green]")
    console.print_json({"data": "example"})

# Get captured content
captured_text = capture.get()

# Export to files
console.export_text("output.txt", styles=True)
console.export_html("output.html", theme="dark")
```

---

## 🖼️ Panels & Layouts (`Panel`)

Panels provide professional bordered containers with extensive customization options.

### Basic Panel Creation
```python
from litprinter import Panel

# Simple panel
panel = Panel(
    "Content goes here",
    title="Main Title",
    subtitle="v1.0",
    border_style="double",
    border_color="cyan"
)
print(panel)
```

### Border Styles and Customization
```python
# Available border styles
styles = ["rounded", "double", "thick", "single", "ascii", "dashed", "dotted", "heavy", "square", "minimal"]

for style in styles:
    panel = Panel(f"Panel with {style} border", title=style.title(), border_style=style)
    print(panel)
```

### Advanced Panel Features
```python
from litprinter import Panel, Padding, Shadow, Background

# Panel with full customization
panel = Panel(
    "Advanced panel content",
    title="Feature Showcase",
    border_style="rounded",
    border_color="bright_blue",
    title_color="white",
    content_color="gray",
    background_color="black",
    padding=Padding.symmetric(1, 2),  # vertical=1, horizontal=2
    margin=Padding.all(1),             # 1 unit on all sides
    width=80,
    height=10,
    align="center",
    vertical_align="middle",
    shadow=Shadow(enabled=True, offset_x=1, offset_y=1, color="gray"),
    overflow="fold"  # Handle text overflow
)
print(panel)
```

### Layout Management with PanelGroup
```python
from litprinter import Panel, PanelGroup

# Vertical layout (default)
v_group = PanelGroup(
    Panel("First panel", title="Panel 1"),
    Panel("Second panel", title="Panel 2"),
    Panel("Third panel", title="Panel 3"),
    layout="vertical",
    spacing=1
)

# Horizontal layout
h_group = PanelGroup(
    Panel("Left", width=30, border_color="cyan"),
    Panel("Right", width=30, border_color="magenta"),
    layout="horizontal",
    spacing=3,
    equal_width=True
)

# Grid layout (2x2)
grid_group = PanelGroup(
    Panel("Top Left", width=25, border_color="red"),
    Panel("Top Right", width=25, border_color="green"),
    Panel("Bottom Left", width=25, border_color="blue"),
    Panel("Bottom Right", width=25, border_color="yellow"),
    layout="grid",
    spacing=2
)

print("Vertical Layout:")
print(v_group.render())
print("\nHorizontal Layout:")
print(h_group.render())
print("\nGrid Layout:")
print(grid_group.render())
```

---

## 💥 Traceback Enhancement

LitPrinter provides beautiful, syntax-highlighted traceback replacements with advanced features.

### Global Installation
```python
from litprinter.traceback import install

# Basic installation
install()

# With custom configuration
install(
    theme="cyberpunk",           # Theme: jarvis, rich, modern, neon, cyberpunk, dracula, monokai, solarized, nord, github, vscode, material, retro, ocean, autumn, synthwave, forest, monochrome, sunset
    show_locals=True,         # Show local variables in each frame
    extra_lines=3,            # Show extra context lines around error
    locals_max_length=150,    # Limit local variable display length
    locals_max_depth=3,       # How deep to format nested structures
    locals_hide_dunder=True,  # Hide __dunder__ variables
    width=120                 # Terminal width for formatting
)
```

### Manual Usage
```python
from litprinter.traceback import PrettyTraceback

try:
    1 / 0
except Exception as e:
    PrettyTraceback.from_exception(*sys.exc_info()).print()
```

---

## 🎨 Themes & Styling

LitPrinter comes with many built-in themes for both console and tracebacks.

### Built-in Themes
- `TokyoNight` (Default)
- `Cyberpunk`
- `Dracula`
- `Monokai`
- `SolarizedDark`
- `Nord`
- `Jarvis`
- `Neon`

### Using Styles
```python
from litprinter import TokyoNight, set_style

set_style(TokyoNight)
```

---

## 🔬 Advanced Usage

### Custom Formatter Registration
```python
from litprinter import argumentToString

class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age

@argumentToString.register(User)
def format_user(user):
    return f"User(name={user.name}, age={user.age})"

# Usage
user = User("Alice", 30)
ic(user)  # Uses custom formatter
```

### Builtin Installation
```python
from litprinter.builtins import install, uninstall

# Install globally
install()  # Makes ic() available without import

# Use anywhere
ic("Available globally!")

# Uninstall when done
uninstall()
```

---

## 🔗 Integration with LLM4Free

LitPrinter is deeply integrated into the LLM4Free ecosystem and used throughout the codebase.

### Usage in LLM4Free
- **Provider debugging**: Used for debugging provider implementations and API calls
- **CLI output**: Powers the rich command-line interface with styled output
- **Search result formatting**: Formats search results with panels and styled content
- **Error reporting**: Enhanced tracebacks for better debugging of issues

### Benefits of Integration
- **Unified styling**: Consistent look and feel across all LLM4Free components
- **Zero dependencies**: No need to install separate debugging libraries
- **Enhanced debugging**: Better error messages and variable inspection throughout the ecosystem

---

## 📚 API Reference

### Core Functions

| Function | Description | Return |
|----------|-------------|--------|
| `ic(*args, **kwargs)` | Debug print with context awareness | Returns first argument |
| `ic.format(*args)` | Format without printing | String |
| `ic.configureOutput(**kwargs)` | Configure global behavior | None |
| `ic.enable()` / `ic.disable()` | Toggle output | None |
| `cprint(text, **kwargs)` | Print with markup support | None |
| `set_style(theme)` | Set global theme | None |
| `install()` / `uninstall()` | Builtin installation | None |

### Classes

| Class | Description | Key Methods |
|-------|-------------|-------------|
| `Console(**kwargs)` | Rich-style terminal output | `print()`, `log()`, `rule()`, `status()`, `capture()` |
| `Panel(content, **kwargs)` | Bordered container | `render()`, styling options |
| `PanelGroup(*panels, **kwargs)` | Layout manager | `render()`, layout options |
| `PrettyTraceback(exc_type, exc_value, tb, **kwargs)` | Enhanced traceback | `print()`, `from_exception()` |

### Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prefix` | str | "ic\|" | Custom prefix for output |
| `includeContext` | bool | True | Show file/line/function context |
| `contextAbsPath` | bool | False | Use absolute paths in context |
| `border_style` | str | "single" | Panel border style |
| `theme` | str | "tokyonight" | Theme name for styling |
| `show_locals` | bool | False | Show local variables in tracebacks |

---

## 🔧 Dependencies

- **Pygments** (optional): Syntax highlighting for tracebacks and code formatting
- **colorama** (Windows): Cross-platform terminal color support
- **Standard library**: `sys`, `os`, `inspect`, `pprint`, `datetime`

---

## 🌈 Supported Python Versions

- Python 3.6+
- Python 3.7, 3.8, 3.9, 3.10, 3.11, 3.12+

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [LLM4Free contributing guidelines](https://github.com/OEvortex/LLM4Free/blob/main/CONTRIBUTING.md) for details.

---

## 📄 License

LitPrinter is released under the MIT License. See [LICENSE](https://github.com/OEvortex/litprinter/blob/main/LICENSE) for details.

---

<div align="center">
  <p>Made with ❤️ by OEvortex</p>
  <p>
    <a href="https://github.com/OEvortex/litprinter">GitHub</a> •
    <a href="https://github.com/OEvortex/LLM4Free">LLM4Free</a> •
    <a href="https://pypi.org/project/litprinter/">PyPI</a>
  </p>
</div>
