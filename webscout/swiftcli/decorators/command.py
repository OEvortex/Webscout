"""Command decorators for SwiftCLI."""

from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from ..core.context import Context


def command(
    name: Optional[str] = None,
    help: Optional[str] = None,
    aliases: Optional[List[str]] = None,
    hidden: bool = False,
) -> Callable:
    """
    Decorator to register a new command.

    This decorator marks a function as a CLI command and provides metadata
    about how command should be registered and displayed.

    Args:
        name: Command name (defaults to function name)
        help: Help text (defaults to function docstring)
        aliases: Alternative names for command
        hidden: Whether to hide from help output

    Example:
        @command(name="greet", help="Say hello")
        def hello(name: str):
            print(f"Hello {name}!")

        @command(aliases=["hi", "hey"])
        def hello(name: str):
            '''Say hello to someone'''
            print(f"Hello {name}!")
    """

    def decorator(f: Callable) -> Callable:
        f._command = {  # type: ignore[attr-defined]
            "name": name or getattr(f, '__name__', 'unknown'),
            "help": help or f.__doc__,
            "aliases": aliases or [],
            "hidden": hidden,
        }
        return f

    return decorator


def group(
    name: Optional[str] = None,
    help: Optional[str] = None,
    chain: bool = False,
    invoke_without_command: bool = False,
) -> Callable:
    """
    Decorator to create a command group.

    Command groups can contain subcommands and optionally chain their results.

    Args:
        name: Group name (defaults to function name)
        help: Help text (defaults to function docstring)
        chain: Whether to chain command results
        invoke_without_command: Allow group to be invoked without subcommand

    Example:
        @group()
        def db():
            '''Database commands'''
            pass

        @db.command()
        def migrate():
            '''Run database migrations'''
            print("Running migrations...")

        @group(chain=True)
        def process():
            '''Process data'''
            pass

        @process.command()
        def validate():
            '''Validate data'''
            return {"valid": True}
    """

    def decorator(f: Callable) -> Callable:
        f._group = {  # type: ignore[attr-defined]
            "name": name or getattr(f, '__name__', 'unknown'),
            "help": help or f.__doc__,
            "chain": chain,
            "invoke_without_command": invoke_without_command,
        }
        return f

    return decorator


def pass_context(f: Callable) -> Callable:
    """
    Decorator to pass CLI context to command.

    This decorator injects current Context object as first argument
    to the decorated command function.

    Example:
        @command()
        @pass_context
        def status(ctx):
            '''Show application status'''
            print(f"App: {ctx.cli.name}")
            print(f"Debug: {ctx.debug}")
    """
    f._pass_context = True  # type: ignore[attr-defined]
    return f


def completion(func: Optional[Callable] = None) -> Callable:
    """
    Decorator to provide shell completion for a command.

    The decorated function should return a list of possible completions
    based on current incomplete value.

    Example:
        @command()
        @option("--service", type=str)
        def restart(service: str):
            '''Restart a service'''
            print(f"Restarting {service}...")

        @restart.completion()
        def complete_service(ctx, incomplete):
            services = ["nginx", "apache", "mysql"]
            return [s for s in services if s.startswith(incomplete)]
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(ctx: Context, incomplete: str) -> List[str]:
            try:
                return f(ctx, incomplete)
            except Exception:
                return []

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


def argument(
    name: str,
    type: Any = str,
    required: bool = True,
    help: Optional[str] = None,
    default: Any = None,
    validation: Optional[Dict[str, Any]] = None,
    mutually_exclusive: Optional[List[str]] = None,
) -> Callable:
    """
    Decorator to add a command argument.

    Arguments are positional parameters that must be provided in order.

    Args:
        name: Argument name
        type: Expected type
        required: Whether argument is required
        help: Help text
        default: Default value if not required
        validation: Dictionary of validation rules (min_length, max_length, pattern, choices, etc.)
        mutually_exclusive: List of argument names that are mutually exclusive with this argument

    Example:
        @command()
        @argument("name", validation={'min_length': 2, 'max_length': 50})
        @argument("count", type=int, default=1, validation={'min': 1, 'max': 100})
        def greet(name: str, count: int):
            '''Greet someone multiple times'''
            for _ in range(count):
                print(f"Hello {name}!")
    """

    def decorator(f: Callable) -> Callable:
        if not hasattr(f, "_arguments"):
            f._arguments = []  # type: ignore[attr-defined]

        f._arguments.append(  # type: ignore[attr-defined]
            {
                "name": name,
                "type": type,
                "required": required,
                "help": help,
                "default": default,
                "validation": validation,
                "mutually_exclusive": mutually_exclusive,
            }
        )
        return f

    return decorator


def flag(name: str, help: Optional[str] = None, hidden: bool = False) -> Callable:
    """
    Decorator to add a boolean flag option.

    Flags are special options that don't take a value - they're either
    present (True) or absent (False).

    Args:
        name: Flag name
        help: Help text
        hidden: Whether to hide from help output

    Example:
        @command()
        @flag("--verbose", help="Enable verbose output")
        def process(verbose: bool):
            '''Process data'''
            if verbose:
                print("Verbose mode enabled")
    """

    def decorator(f: Callable) -> Callable:
        if not hasattr(f, "_options"):
            f._options = []  # type: ignore[attr-defined]

        f._options.append(  # type: ignore[attr-defined]
            {
                "param_decls": [name],
                "is_flag": True,
                "help": help,
                "hidden": hidden,
            }
        )
        return f

    return decorator
