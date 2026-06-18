"""Decorators for SwiftCLI."""

from .command import argument, command, flag, group, pass_context
from .options import config_file, envvar, help_option, option, version_option
from .output import format_output, pager_output, panel_output, progress, table_output

__all__ = [
    # Command decorators
    'command',
    'group',
    'argument',
    'flag',
    'pass_context',

    # Option decorators
    'option',
    'envvar',
    'config_file',
    'version_option',
    'help_option',

    # Output decorators
    'table_output',
    'progress',
    'panel_output',
    'format_output',
    'pager_output'
]
