"""Utility functions for text formatting and styling."""

import re
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

console = Console()

def style_text(
    text: str,
    color: Optional[str] = None,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False
) -> Text:
    """
    Apply styling to text.

    Args:
        text: Text to style
        color: Text color
        bold: Bold text
        italic: Italic text
        underline: Underline text

    Returns:
        Rich Text object with applied styling
    """
    style = []
    if color:
        style.append(color)
    if bold:
        style.append("bold")
    if italic:
        style.append("italic")
    if underline:
        style.append("underline")

    return Text(text, style=" ".join(style))

def format_error(message: str, title: str = "Error") -> None:
    """
    Format and display error message.

    Args:
        message: Error message
        title: Error title
    """
    console.print(f"[bold red]{title}:[/] {message}")

def format_warning(message: str, title: str = "Warning") -> None:
    """
    Format and display warning message.

    Args:
        message: Warning message
        title: Warning title
    """
    console.print(f"[bold yellow]{title}:[/] {message}")

def format_success(message: str, title: str = "Success") -> None:
    """
    Format and display success message.

    Args:
        message: Success message
        title: Success title
    """
    console.print(f"[bold green]{title}:[/] {message}")

def format_info(message: str, title: str = "Info") -> None:
    """
    Format and display info message.

    Args:
        message: Info message
        title: Info title
    """
    console.print(f"[bold blue]{title}:[/] {message}")

def create_table(
    headers: List[str],
    rows: List[List[Any]],
    title: Optional[str] = None,
    style: str = "default",
    show_lines: bool = False
) -> Table:
    """
    Create a formatted table.

    Args:
        headers: Column headers
        rows: Table rows
        title: Table title
        style: Table style
        show_lines: Show row/column lines

    Returns:
        Rich Table object
    """
    table = Table(
        title=title,
        show_header=True,
        header_style="bold blue",
        show_lines=show_lines
    )

    # Add columns
    for header in headers:
        table.add_column(header)

    # Add rows
    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    return table

def truncate_text(
    text: str,
    max_length: int,
    suffix: str = "..."
) -> str:
    """
    Truncate text to specified length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Truncation suffix

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def wrap_text(
    text: str,
    width: int,
    indent: str = "",
    initial_indent: str = ""
) -> str:
    """
    Wrap text to specified width.

    Args:
        text: Text to wrap
        width: Maximum line width
        indent: Indentation for wrapped lines
        initial_indent: Indentation for first line

    Returns:
        Wrapped text
    """
    import textwrap
    return textwrap.fill(
        text,
        width=width,
        initial_indent=initial_indent,
        subsequent_indent=indent
    )

def format_dict(
    data: Dict[str, Any],
    indent: int = 2,
    sort_keys: bool = True
) -> str:
    """
    Format dictionary for display.

    Args:
        data: Dictionary to format
        indent: Indentation level
        sort_keys: Sort dictionary keys

    Returns:
        Formatted string
    """
    import json
    return json.dumps(
        data,
        indent=indent,
        sort_keys=sort_keys,
        default=str
    )

def format_list(
    items: List[Any],
    bullet: str = "•",
    indent: int = 2
) -> str:
    """
    Format list for display.

    Args:
        items: List to format
        bullet: Bullet point character
        indent: Indentation level

    Returns:
        Formatted string
    """
    indent_str = " " * indent
    return "\n".join(f"{indent_str}{bullet} {item}" for item in items)

def strip_ansi(text: str) -> str:
    """
    Remove ANSI escape sequences from text.

    Args:
        text: Text containing ANSI sequences

    Returns:
        Clean text
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def get_terminal_size() -> tuple:
    """
    Get terminal size.

    Returns:
        Tuple of (width, height)
    """
    return console.size

def clear_screen() -> None:
    """Clear the terminal screen."""
    console.clear()

def create_padding(
    renderable: Any,
    pad: Union[int, tuple] = 1
) -> Padding:
    """
    Add padding around content.

    Args:
        renderable: Content to pad
        pad: Padding amount

    Returns:
        Padded content
    """
    return Padding(renderable, pad)
