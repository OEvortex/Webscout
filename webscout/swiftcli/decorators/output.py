"""Output formatting decorators for SwiftCLI."""

import json
from functools import wraps
from typing import TYPE_CHECKING, Callable, List, Optional, Union

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeRemainingColumn,
    )
else:
    # Handle different versions of rich
    try:
        from rich.progress import (
            BarColumn,
            Progress,
            SpinnerColumn,
            TaskProgressColumn,
            TextColumn,
            TimeRemainingColumn,
        )
    except ImportError:
        # If standard imports fail, try older rich versions or create minimal fallbacks
        try:
            from rich.progress import (
                BarColumn,
                Progress,
                SpinnerColumn,
                TextColumn,
                TimeRemainingColumn,
            )

            # Create a simple TaskProgressColumn replacement for older versions
            class TaskProgressColumn:
                def __init__(self):
                    pass

                def __call__(self, task):
                    return f"{task.percentage:.1f}%"
        except ImportError:
            # If rich is too old or not installed, create minimal fallbacks
            class Progress:
                def __init__(self, *args, **kwargs):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

                def add_task(self, description, total=None):
                    return 0

                def update(self, task_id, **kwargs):
                    pass

            class SpinnerColumn:
                pass

            class TextColumn:
                def __init__(self, text):
                    pass

            class BarColumn:
                pass

            class TaskProgressColumn:
                pass

            class TimeRemainingColumn:
                pass


console = Console()


def table_output(
    headers: List[str],
    title: Optional[str] = None,
    style: str = "default",
    show_lines: bool = False,
    expand: bool = False,
) -> Callable:
    """
    Decorator to format command output as a table.

    Args:
        headers: Column headers
        title: Table title
        style: Table style
        show_lines: Show row/column lines
        expand: Expand table to terminal width

    Example:
        @command()
        @table_output(["ID", "Name", "Status"])
        def list_users():
            '''List all users'''
            return [
                [1, "John", "Active"],
                [2, "Jane", "Inactive"]
            ]
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if result:
                table = Table(
                    title=title,
                    show_header=True,
                    header_style="bold blue",
                    show_lines=show_lines,
                    expand=expand,
                )

                # Add columns
                for header in headers:
                    table.add_column(header)

                # Add rows
                for row in result:
                    table.add_row(*[str(cell) for cell in row])

                console.print(table)
            return result

        return wrapper

    return decorator


def json_output(indent: int = 2, sort_keys: bool = False, ensure_ascii: bool = False) -> Callable:
    """
    Decorator to format command output as JSON.

    Args:
        indent: Indentation level for pretty printing
        sort_keys: Whether to sort dictionary keys
        ensure_ascii: Whether to escape non-ASCII characters

    Example:
        @command()
        @json_output(indent=2)
        def get_data():
            '''Get data as JSON'''
            return {"status": "success", "data": [1, 2, 3]}
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if result:
                json_str = json.dumps(
                    result, indent=indent, sort_keys=sort_keys, ensure_ascii=ensure_ascii
                )
                console.print(json_str)
            return result

        return wrapper

    return decorator


def yaml_output(default_flow_style: bool = False, sort_keys: bool = False) -> Callable:
    """
    Decorator to format command output as YAML.

    Args:
        default_flow_style: Whether to use flow style for collections
        sort_keys: Whether to sort dictionary keys

    Example:
        @command()
        @yaml_output()
        def get_config():
            '''Get configuration as YAML'''
            return {"database": {"host": "localhost", "port": 5432}}
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if result:
                yaml_str = yaml.safe_dump(
                    result, default_flow_style=default_flow_style, sort_keys=sort_keys
                )
                console.print(yaml_str)
            return result

        return wrapper

    return decorator


def progress(
    description: Optional[str] = None,
    total: Optional[int] = None,
    transient: bool = False,
    show_bar: bool = True,
    show_percentage: bool = True,
    show_time: bool = True,
) -> Callable:
    """
    Decorator to show progress for long-running commands.

    The decorated function should be a generator that yields
    progress updates.

    Args:
        description: Task description
        total: Total number of steps
        transient: Remove progress when done
        show_bar: Show progress bar
        show_percentage: Show percentage complete
        show_time: Show time remaining

    Example:
        @command()
        @progress("Processing files")
        def process(files: List[str]):
            '''Process multiple files'''
            for file in files:
                # Process file
                yield f"Processing {file}..."
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            columns = []
            columns.append(SpinnerColumn())
            columns.append(TextColumn("[progress.description]{task.description}"))

            if show_bar:
                columns.append(BarColumn())
            if show_percentage:
                try:
                    columns.append(TaskProgressColumn())
                except Exception:
                    # Fallback for older rich versions
                    columns.append(TextColumn("[progress.percentage]{task.percentage:>3.0f}%"))
            if show_time:
                columns.append(TimeRemainingColumn())

            with Progress(*columns, transient=transient) as progress:
                task = progress.add_task(description or getattr(f, '__name__', 'unknown'), total=total)

                try:
                    for update in f(*args, **kwargs):
                        if isinstance(update, (int, float)):
                            # Update progress by number
                            progress.update(task, advance=update)
                        elif isinstance(update, str):
                            # Update description
                            progress.update(task, description=update)
                        elif isinstance(update, dict):
                            # Update multiple attributes
                            progress.update(task, **update)
                        else:
                            # Just advance by 1
                            progress.update(task, advance=1)
                except Exception as e:
                    progress.update(task, description=f"Error: {str(e)}")
                    raise
                finally:
                    progress.update(task, completed=total or 100)

        return wrapper

    return decorator


def panel_output(
    title: Optional[str] = None,
    style: str = "default",
    expand: bool = True,
    padding: Union[int, tuple] = 1,
) -> Callable:
    """
    Decorator to display command output in a panel.

    Args:
        title: Panel title
        style: Panel style
        expand: Expand panel to terminal width
        padding: Panel padding

    Example:
        @command()
        @panel_output(title="System Status")
        def status():
            '''Show system status'''
            return "All systems operational"
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if result:
                panel = Panel(str(result), title=title, style=style, expand=expand, padding=padding)
                console.print(panel)
            return result

        return wrapper

    return decorator


def format_output(template: str, style: Optional[str] = None) -> Callable:
    """
    Decorator to format command output using a template.

    Args:
        template: Format string template
        style: Rich style string

    Example:
        @command()
        @format_output("Created user {name} with ID {id}")
        def create_user(name: str):
            '''Create a new user'''
            return {"name": name, "id": 123}
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if result:
                if isinstance(result, dict):
                    output = template.format(**result)
                else:
                    output = template.format(result)

                if style:
                    console.print(output, style=style)
                else:
                    console.print(output)
            return result

        return wrapper

    return decorator


def pager_output(use_pager: bool = True, style: Optional[str] = None) -> Callable:
    """
    Decorator to display command output in a pager.

    Args:
        use_pager: Whether to use pager
        style: Rich style string

    Example:
        @command()
        @pager_output()
        def show_logs():
            '''Show application logs'''
            return "Very long log output..."
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if result:
                with console.pager(styles=use_pager):
                    if style:
                        console.print(result, style=style)
                    else:
                        console.print(result)
            return result

        return wrapper

    return decorator
