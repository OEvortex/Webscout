"""Base plugin system for SwiftCLI."""

from typing import Any, Dict, List, Optional


class Plugin:
    """
    Base class for SwiftCLI plugins.

    Plugins can extend the CLI functionality by hooking into various stages
    of command execution. Subclass this class and override the methods
    you want to hook into.

    Attributes:
        app: The CLI application instance
        enabled: Whether the plugin is enabled
        config: Plugin configuration dictionary

    Example:
        class LoggingPlugin(Plugin):
            def before_command(self, command, args):
                print(f"[LOG] Running command: {command}")

            def after_command(self, command, args, result):
                print(f"[LOG] Command completed: {result}")
    """

    def __init__(self):
        self.app = None  # Set by plugin manager
        self.enabled: bool = True
        self.config: Dict[str, Any] = {}

    def init_app(self, app: Any) -> None:
        """
        Initialize plugin with CLI app instance.

        Args:
            app: The CLI application instance
        """
        self.app = app

    def before_command(self, command: str, args: List[str]) -> Optional[bool]:
        """
        Called before command execution.

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Optional[bool]: Return False to prevent command execution
        """
        pass

    def after_command(self, command: str, args: List[str], result: Any) -> None:
        """
        Called after command execution.

        Args:
            command: Command name
            args: Command arguments
            result: Command result
        """
        pass

    def on_error(self, command: str, error: Exception) -> None:
        """
        Called when command raises an error.

        Args:
            command: Command name
            error: The exception that was raised
        """
        pass

    def on_help(self, command: str) -> Optional[str]:
        """
        Called when help is requested for a command.

        Args:
            command: Command name

        Returns:
            Optional[str]: Additional help text to display
        """
        pass

    def on_completion(self, command: str, incomplete: str) -> List[str]:
        """
        Called when shell completion is requested.

        Args:
            command: Command name
            incomplete: Incomplete text to complete

        Returns:
            List[str]: Possible completions
        """
        return []

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the plugin.

        Args:
            config: Configuration dictionary
        """
        self.config.update(config)

    def validate_config(self) -> None:
        """
        Validate plugin configuration.

        Raises:
            PluginError: If configuration is invalid
        """
        pass

    def enable(self) -> None:
        """Enable the plugin."""
        self.enabled = True

    def disable(self) -> None:
        """Disable the plugin."""
        self.enabled = False

    @property
    def name(self) -> str:
        """Get plugin name."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"<{self.name} [{status}]>"
