"""Command group handling for SwiftCLI."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from rich.console import Console

from ..utils.formatting import format_error
from .context import Context

if TYPE_CHECKING:
    from .cli import CLI

console = Console()


class Group:
    """
    Command group that can contain subcommands.

    Groups allow organizing related commands together and support command
    chaining for building command pipelines.

    Attributes:
        name: Group name
        help: Group description
        commands: Registered commands
        parent: Parent CLI instance
        chain: Enable command chaining
        invoke_without_command: Allow invoking group without subcommand

    Example:
        @app.group()
        def db():
            '''Database commands'''
            pass

        @db.command()
        def migrate():
            '''Run database migrations'''
            print("Running migrations...")
    """

    def __init__(
        self,
        name: str,
        help: Optional[str] = None,
        parent: Optional["CLI"] = None,
        chain: bool = False,
        invoke_without_command: bool = False,
    ):
        """
        Initialize command group.

        Args:
            name: Group name
            help: Group description
            parent: Parent CLI instance
            chain: Enable command chaining
            invoke_without_command: Allow invoking group without subcommand
        """
        self.name = name
        self.help = help
        self.parent = parent
        self.chain = chain
        self.invoke_without_command = invoke_without_command
        self.commands: Dict[str, Any] = {}

    def command(
        self,
        name: Optional[str] = None,
        help: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        hidden: bool = False,
    ):
        """
        Decorator to register a command in this group.

        Args:
            name: Command name (defaults to function name)
            help: Command help text
            aliases: Alternative command names
            hidden: Hide from help output

        Example:
            @group.command()
            def status():
                '''Show status'''
                print("Status: OK")
        """

        def decorator(f):
            cmd_name = name or f.__name__
            self.commands[cmd_name] = {
                "name": cmd_name,
                "func": f,
                "help": help or f.__doc__,
                "aliases": aliases or [],
                "hidden": hidden,
            }

            # Register aliases
            for alias in aliases or []:
                self.commands[alias] = self.commands[cmd_name]

            return f

        return decorator

    def group(self, name: Optional[str] = None, help: Optional[str] = None, **kwargs):
        """
        Create a subgroup within this group.

        Args:
            name: Subgroup name
            help: Subgroup help text
            **kwargs: Additional group options

        Example:
            @group.group()
            def config():
                '''Configuration commands'''
                pass
        """

        def decorator(f):
            subgroup = Group(
                name=name or f.__name__, help=help or f.__doc__, parent=self.parent, **kwargs
            )
            self.commands[subgroup.name] = subgroup
            return subgroup

        return decorator

    def run(self, args: List[str]) -> int:
        """
        Run a command in this group.

        Args:
            args: Command arguments

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Show help if no arguments or help requested
            if not args or args[0] in ["-h", "--help"]:
                self._print_help()
                return 0

            command_name = args[0]
            command_args = args[1:]

            # Check if command exists
            if command_name not in self.commands:
                format_error(f"Unknown command: {self.name} {command_name}")
                self._print_help()
                return 1

            command = self.commands[command_name]

            # Handle nested groups
            if isinstance(command, Group):
                return command.run(command_args)

            # Create command context - parent is a CLI instance, never None at this point
            # Context expects CLI type, and self.parent should be set when group is created by CLI
            cli = self.parent
            ctx = Context(
                cli,
                command=f"{self.name} {command_name}",
                debug=getattr(self.parent, "debug", False) if self.parent else False,
            )

            # Run command through plugin system
            if self.parent and not self.parent.plugin_manager.before_command(
                f"{self.name} {command_name}", command_args
            ):
                return 1

            try:
                import asyncio
                import inspect

                func = command["func"]
                params = self._parse_args(command, command_args)

                # Inject context if function was decorated with pass_context
                if getattr(func, "_pass_context", False):
                    call_args = (ctx,)
                else:
                    call_args = ()

                # If coroutine function, run it using asyncio
                if inspect.iscoroutinefunction(func):
                    result = asyncio.run(func(*call_args, **params))
                else:
                    result = func(*call_args, **params)

                # If function returned a coroutine-like object
                if not inspect.iscoroutine(result) and hasattr(result, "__await__"):
                    result = asyncio.run(result)

                if self.parent:
                    self.parent.plugin_manager.after_command(
                        f"{self.name} {command_name}", command_args, result
                    )

                # Handle command chaining
                if self.chain and result is not None:
                    return result if isinstance(result, int) else 0

                return 0

            except Exception as e:
                if self.parent:
                    self.parent.plugin_manager.on_error(f"{self.name} {command_name}", e)
                if getattr(self.parent, "debug", False):
                    raise
                format_error(str(e))
                return 1

        except Exception as e:
            if getattr(self.parent, "debug", False):
                raise
            format_error(str(e))
            return 1

    def _parse_args(self, command: Dict[str, Any], args: List[str]) -> Dict[str, Any]:
        """Parse command arguments."""
        # Use parent CLI's argument parser if available
        if self.parent:
            return self.parent._parse_args(command, args)

        # Fallback to basic argument parsing
        from ..utils.parsing import parse_args

        return parse_args(args)

    def _print_help(self) -> None:
        """Print group help message."""
        console.print(f"\n[bold]{self.name}[/] - {self.help or ''}")

        console.print("\n[bold]Commands:[/]")
        printed = set()
        for name, cmd in self.commands.items():
            # cmd can be a Group or a dict mapping
            if isinstance(cmd, Group):
                primary = cmd.name
                if primary in printed:
                    continue
                printed.add(primary)
                console.print(f"  {primary} [group]")
                if cmd.help:
                    console.print(f"    {cmd.help}")
            elif isinstance(cmd, dict):
                primary = cmd.get("name", name)
                if primary in printed:
                    continue
                printed.add(primary)
                if not cmd.get("hidden", False):
                    aliases = cmd.get("aliases", [])
                    alias_text = f" (aliases: {', '.join(aliases)})" if aliases else ""
                    console.print(f"  {primary:20} {cmd['help'] or ''}{alias_text}")

        console.print("\nUse -h or --help with any command for more info")

    def __repr__(self) -> str:
        return f"<Group name={self.name}>"
