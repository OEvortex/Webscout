"""Context handling for SwiftCLI."""

from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from .cli import CLI


class Context:
    """
    Context object that holds state for the CLI app.

    The Context class provides access to the CLI application instance and maintains
    state throughout command execution. It can be used to pass data between
    commands and access global configuration.

    Attributes:
        cli: The CLI application instance.
        parent: The parent context if this is a subcommand.
        command: The current command name.
        obj: An object that can be used to store arbitrary data.
        params: Dictionary of current command parameters.
        debug: Debug mode flag.

    Example:
        @app.command()
        @pass_context
        def status(ctx):
            '''Show application status'''
            print(f"App: {ctx.cli.name}")
            print(f"Debug: {ctx.debug}")
    """

    def __init__(
        self,
        cli: Optional["CLI"] = None,
        parent: Optional["Context"] = None,
        command: Optional[str] = None,
        obj: Any = None,
        debug: bool = False,
    ):
        self.cli = cli
        self.parent = parent
        self.command = command
        self.obj = obj
        self.params: Dict[str, Any] = {}
        self.debug = debug

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """
        Get a parameter value from the context.

        Args:
            name: Parameter name
            default: Default value if parameter not found

        Returns:
            Parameter value or default
        """
        return self.params.get(name, default)

    def set_parameter(self, name: str, value: Any) -> None:
        """
        Set a parameter value in the context.

        Args:
            name: Parameter name
            value: Parameter value
        """
        self.params[name] = value

    def get_parent_context(self) -> Optional["Context"]:
        """Get the parent context if it exists."""
        return self.parent

    def create_child_context(self, command: Optional[str] = None, obj: Any = None) -> "Context":
        """
        Create a new child context.

        Args:
            command: Command name for the child context
            obj: Object to store in child context

        Returns:
            New child context
        """
        return Context(cli=self.cli, parent=self, command=command, obj=obj, debug=self.debug)

    @property
    def root_context(self) -> "Context":
        """Get the root context by traversing up the parent chain."""
        ctx = self
        while ctx.parent is not None:
            ctx = ctx.parent
        return ctx

    def __repr__(self) -> str:
        return f"<Context command={self.command}>"
