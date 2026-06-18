"""Core functionality for SwiftCLI."""

from .cli import CLI
from .context import Context
from .group import Group

__all__ = ['CLI', 'Context', 'Group']
