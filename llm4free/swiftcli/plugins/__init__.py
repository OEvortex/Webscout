"""Plugin system for SwiftCLI."""

from .base import Plugin
from .manager import PluginManager

__all__ = [
    'Plugin',
    'PluginManager'
]
