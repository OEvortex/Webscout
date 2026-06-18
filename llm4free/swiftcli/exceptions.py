"""Exception classes for SwiftCLI."""

class SwiftCLIException(Exception):
    """Base exception class for SwiftCLI."""
    pass

class UsageError(SwiftCLIException):
    """Raised when CLI is used incorrectly."""
    pass

class BadParameter(UsageError):
    """Raised when a parameter is invalid."""
    pass

class ConfigError(SwiftCLIException):
    """Raised when there is a configuration error."""
    pass

class PluginError(SwiftCLIException):
    """Raised when there is a plugin error."""
    pass
