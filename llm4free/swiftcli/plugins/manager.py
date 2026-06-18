"""Plugin manager for SwiftCLI."""

import importlib
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from ..exceptions import PluginError
from .base import Plugin

console = Console()

class PluginManager:
    """
    Manages SwiftCLI plugins.

    The plugin manager handles plugin registration, loading, and execution.
    It provides hooks for plugins to extend CLI functionality at various points
    during command execution.

    Attributes:
        plugins: List of registered plugins
        plugin_dir: Directory where plugins are stored

    Example:
        # Register a plugin
        plugin_manager = PluginManager()
        plugin_manager.register(LoggingPlugin())

        # Load plugins from directory
        plugin_manager.load_plugins()
    """

    def __init__(self, plugin_dir: Optional[str] = None):
        """
        Initialize plugin manager.

        Args:
            plugin_dir: Optional custom plugin directory path
        """
        self.plugins: List[Plugin] = []
        # Use temporary directory instead of ~/.swiftcli/plugins
        if plugin_dir:
            self.plugin_dir = plugin_dir
            os.makedirs(self.plugin_dir, exist_ok=True)
        else:
            # Create a temporary directory that will be cleaned up when the process exits
            self.temp_dir = tempfile.TemporaryDirectory(prefix="swiftcli_")
            self.plugin_dir = self.temp_dir.name

        # Add plugin directory to Python path
        if self.plugin_dir not in sys.path:
            sys.path.append(self.plugin_dir)

    def register(self, plugin: Plugin) -> None:
        """
        Register a new plugin.

        Args:
            plugin: Plugin instance to register

        Raises:
            PluginError: If plugin is invalid or already registered
        """
        if not isinstance(plugin, Plugin):
            raise PluginError(f"Invalid plugin type: {type(plugin)}")

        if self._get_plugin(plugin.name):
            raise PluginError(f"Plugin already registered: {plugin.name}")

        try:
            plugin.validate_config()
        except Exception as e:
            raise PluginError(f"Plugin configuration invalid: {str(e)}")

        self.plugins.append(plugin)

    def unregister(self, plugin_name: str) -> None:
        """
        Unregister a plugin.

        Args:
            plugin_name: Name of plugin to unregister

        Raises:
            PluginError: If plugin not found
        """
        plugin = self._get_plugin(plugin_name)
        if not plugin:
            raise PluginError(f"Plugin not found: {plugin_name}")

        self.plugins.remove(plugin)

    def load_plugins(self) -> None:
        """
        Load all plugins from plugin directory.

        This method searches for Python files in the plugin directory and
        attempts to load any Plugin subclasses defined in them.
        """
        for file in Path(self.plugin_dir).glob("*.py"):
            if file.name.startswith("_"):
                continue

            try:
                module = importlib.import_module(file.stem)

                # Find Plugin subclasses in module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, Plugin) and
                        attr is not Plugin):
                        plugin = attr()
                        self.register(plugin)

            except Exception as e:
                console.print(f"[red]Error loading plugin {file.name}: {e}[/red]")

    def init_plugins(self, app: Any) -> None:
        """
        Initialize all plugins with the CLI application instance.

        Args:
            app: The CLI application instance
        """
        for plugin in self.plugins:
            plugin.init_app(app)

    def configure_plugins(self, config: Dict[str, Dict[str, Any]]) -> None:
        """
        Configure plugins with provided configuration.

        Args:
            config: Dictionary of plugin configurations
        """
        for plugin in self.plugins:
            if plugin.name in config:
                plugin.configure(config[plugin.name])

    def before_command(self, command: str, args: List[str]) -> bool:
        """
        Run before_command hooks for all plugins.

        Args:
            command: Command name
            args: Command arguments

        Returns:
            bool: False if any plugin prevents command execution
        """
        for plugin in self.plugins:
            if not plugin.enabled:
                continue

            try:
                result = plugin.before_command(command, args)
                if result is False:
                    return False
            except Exception as e:
                console.print(f"[red]Error in plugin {plugin.name}: {e}[/red]")
                if plugin.app and getattr(plugin.app, 'debug', False):
                    import traceback
                    traceback.print_exc()

        return True

    def after_command(self, command: str, args: List[str], result: Any) -> None:
        """
        Run after_command hooks for all plugins.

        Args:
            command: Command name
            args: Command arguments
            result: Command result
        """
        for plugin in self.plugins:
            if not plugin.enabled:
                continue

            try:
                plugin.after_command(command, args, result)
            except Exception as e:
                console.print(f"[red]Error in plugin {plugin.name}: {e}[/red]")
                if plugin.app and getattr(plugin.app, 'debug', False):
                    import traceback
                    traceback.print_exc()

    def on_error(self, command: str, error: Exception) -> None:
        """
        Run error hooks for all plugins.

        Args:
            command: Command name
            error: The exception that was raised
        """
        for plugin in self.plugins:
            if not plugin.enabled:
                continue

            try:
                plugin.on_error(command, error)
            except Exception as e:
                console.print(f"[red]Error in plugin {plugin.name}: {e}[/red]")
                if plugin.app and getattr(plugin.app, 'debug', False):
                    import traceback
                    traceback.print_exc()

    def get_help_text(self, command: str) -> List[str]:
        """
        Get additional help text from plugins.

        Args:
            command: Command name

        Returns:
            List[str]: List of help text strings from plugins
        """
        help_texts = []
        for plugin in self.plugins:
            if not plugin.enabled:
                continue

            try:
                help_text = plugin.on_help(command)
                if help_text:
                    help_texts.append(help_text)
            except Exception as e:
                console.print(f"[red]Error in plugin {plugin.name}: {e}[/red]")

        return help_texts

    def get_completions(self, command: str, incomplete: str) -> List[str]:
        """
        Get command completions from plugins.

        Args:
            command: Command name
            incomplete: Incomplete text to complete

        Returns:
            List[str]: Combined list of completions from all plugins
        """
        completions = []
        for plugin in self.plugins:
            if not plugin.enabled:
                continue

            try:
                plugin_completions = plugin.on_completion(command, incomplete)
                completions.extend(plugin_completions)
            except Exception as e:
                console.print(f"[red]Error in plugin {plugin.name}: {e}[/red]")

        return list(set(completions))  # Remove duplicates

    def _get_plugin(self, name: str) -> Optional[Plugin]:
        """Get plugin by name."""
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        return None

    def __repr__(self) -> str:
        return f"<PluginManager plugins={len(self.plugins)}>"
