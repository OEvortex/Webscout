"""Utility functions for parsing and validating command-line arguments."""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

import yaml

from ..exceptions import BadParameter, UsageError


def parse_args(args: List[str]) -> Dict[str, Any]:
    """
    Parse command line arguments into a dictionary.

    Args:
        args: List of command line arguments

    Returns:
        Dictionary of parsed arguments

    Example:
        >>> parse_args(['--name', 'test', '--flag', '-n', '42'])
        {'name': 'test', 'flag': True, 'n': '42'}
    """
    parsed = {}
    i = 0
    while i < len(args):
        arg = args[i]

        # Handle flags/options
        if arg.startswith('-'):
            # Support --key=value or -k=value syntax
            if '=' in arg:
                key, value = arg.lstrip('-').split('=', 1)
                key = key.replace('-', '_')
            else:
                key = arg.lstrip('-').replace('-', '_')

                # Check if next arg is a value or another flag
                if i + 1 >= len(args) or args[i + 1].startswith('-'):
                    value = True  # Flag without value
                else:
                    value = args[i + 1]
                    i += 1

            # Support repeated flags/options by turning into lists
            if key in parsed:
                existing = parsed[key]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    parsed[key] = [existing, value]
            else:
                parsed[key] = value
        else:
            # Positional argument
            pos_index = len([k for k in parsed.keys() if k.startswith('arg')])
            parsed[f'arg{pos_index}'] = arg

        i += 1

    return parsed

def validate_required(
    params: Dict[str, Any],
    required: List[str]
) -> None:
    """
    Validate required parameters are present.

    Args:
        params: Parameter dictionary
        required: List of required parameter names

    Raises:
        UsageError: If required parameter is missing
    """
    missing = [p for p in required if p not in params]
    if missing:
        raise UsageError(f"Missing required parameters: {', '.join(missing)}")

def convert_type(
    value: str,
    type_: Type,
    param_name: str
) -> Any:
    """
    Convert string value to specified type.

    Args:
        value: String value to convert
        type_: Target type
        param_name: Parameter name for error messages

    Returns:
        Converted value

    Raises:
        BadParameter: If conversion fails
    """
    try:
        # Handle boolean conversion robustly when the input may already be a bool
        if type_ is bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                return value.lower() in ('true', 't', 'yes', 'y', '1')
            return bool(value)

        # If a list is provided and the target type is a collection type, return as-is
        if isinstance(value, list) and getattr(type_, '__origin__', None) in (list,):
            return value

        # Attempt to construct the type normally (e.g., int('42'), Enum('val'), etc.)
        return type_(value)
    except (ValueError, TypeError):
        raise BadParameter(
            f"Invalid value for {param_name}: {value} (expected {type_.__name__})"
        )

def validate_choice(
    value: Any,
    choices: List[Any],
    param_name: str,
    case_sensitive: bool = True
) -> None:
    """
    Validate value is one of allowed choices.

    Args:
        value: Value to validate
        choices: List of allowed choices
        param_name: Parameter name for error messages
        case_sensitive: Whether to do case-sensitive comparison

    Raises:
        BadParameter: If value not in choices
    """
    if not case_sensitive and isinstance(value, str):
        if value.lower() not in [str(c).lower() for c in choices]:
            raise BadParameter(
                f"Invalid choice for {param_name}: {value} "
                f"(choose from {', '.join(str(c) for c in choices)})"
            )
    elif value not in choices:
        raise BadParameter(
            f"Invalid choice for {param_name}: {value} "
            f"(choose from {', '.join(str(c) for c in choices)})"
        )

def validate_argument(
    value: str,
    validation_rules: Dict[str, Any],
    param_name: str
) -> str:
    """
    Validate argument against validation rules.

    Args:
        value: Argument value to validate
        validation_rules: Dictionary of validation rules
        param_name: Parameter name for error messages

    Returns:
        Validated value

    Raises:
        BadParameter: If validation fails
    """
    if not value and validation_rules.get('required', True):
        raise BadParameter(f"Required argument {param_name} is empty")

    if 'min_length' in validation_rules and len(value) < validation_rules['min_length']:
        raise BadParameter(
            f"Argument {param_name} too short (min {validation_rules['min_length']} characters)"
        )

    if 'max_length' in validation_rules and len(value) > validation_rules['max_length']:
        raise BadParameter(
            f"Argument {param_name} too long (max {validation_rules['max_length']} characters)"
        )

    if 'pattern' in validation_rules:
        pattern = validation_rules['pattern']
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        if not pattern.match(value):
            raise BadParameter(
                f"Argument {param_name} doesn't match pattern: {validation_rules.get('pattern', pattern.pattern)}"
            )

    if 'choices' in validation_rules:
        validate_choice(value, validation_rules['choices'], param_name,
                      validation_rules.get('case_sensitive', True))

    return value

def check_mutually_exclusive(
    params: Dict[str, Any],
    exclusive_groups: List[List[str]]
) -> None:
    """
    Check that mutually exclusive options are not used together.

    Args:
        params: Dictionary of parsed parameters
        exclusive_groups: List of option groups that are mutually exclusive

    Raises:
        UsageError: If mutually exclusive options are used together
    """
    for group in exclusive_groups:
        provided_options = [opt for opt in group if opt in params and params[opt] is not None]
        if len(provided_options) > 1:
            raise UsageError(
                f"Options {', '.join(provided_options)} are mutually exclusive "
                f"and cannot be used together"
            )

def load_config_file(
    path: Union[str, Path],
    format: str = 'auto',
    required: bool = True
) -> Dict[str, Any]:
    """
    Load configuration from file.

    Args:
        path: Path to config file
        format: File format (json, yaml, or auto)
        required: Whether file is required

    Returns:
        Configuration dictionary

    Raises:
        UsageError: If required file not found or invalid format
    """
    path = Path(os.path.expanduser(path))

    if not path.exists():
        if required:
            raise UsageError(f"Config file not found: {path}")
        return {}

    # Auto-detect format from extension
    if format == 'auto':
        format = path.suffix.lstrip('.').lower()
        if format not in ('json', 'yaml', 'yml'):
            raise UsageError(f"Unsupported config format: {format}")

    try:
        with open(path) as f:
            if format == 'json':
                return json.load(f)
            elif format in ('yaml', 'yml'):
                return yaml.safe_load(f)
            else:
                raise UsageError(f"Unsupported config format: {format}")
    except Exception as e:
        raise UsageError(f"Error loading config file: {str(e)}")

def parse_key_value(
    value: str,
    separator: str = '='
) -> tuple:
    """
    Parse key-value string.

    Args:
        value: String in format "key=value"
        separator: Key-value separator

    Returns:
        Tuple of (key, value)

    Raises:
        BadParameter: If string not in key=value format
    """
    try:
        key, value = value.split(separator, 1)
        return key.strip(), value.strip()
    except ValueError:
        raise BadParameter(
            f"Invalid key-value pair: {value} (expected format: key{separator}value)"
        )

def parse_list(
    value: str,
    separator: str = ','
) -> List[str]:
    """
    Parse comma-separated list.

    Args:
        value: Comma-separated string
        separator: List item separator

    Returns:
        List of strings
    """
    return [x.strip() for x in value.split(separator) if x.strip()]

def parse_dict(
    value: str,
    item_separator: str = ',',
    key_value_separator: str = '='
) -> Dict[str, str]:
    """
    Parse dictionary string.

    Args:
        value: String in format "key1=value1,key2=value2"
        item_separator: Separator between items
        key_value_separator: Separator between keys and values

    Returns:
        Dictionary of key-value pairs

    Example:
        >>> parse_dict("name=test,count=42")
        {'name': 'test', 'count': '42'}
    """
    result = {}
    if not value:
        return result

    items = parse_list(value, item_separator)
    for item in items:
        key, value = parse_key_value(item, key_value_separator)
        result[key] = value

    return result

def get_env_var(
    name: str,
    type_: Type = str,
    required: bool = False,
    default: Any = None
) -> Any:
    """
    Get and validate environment variable.

    Args:
        name: Environment variable name
        type_: Expected type
        required: Whether variable is required
        default: Default value if not set

    Returns:
        Environment variable value

    Raises:
        UsageError: If required variable not set
    """
    value = os.environ.get(name)

    if value is None:
        if required:
            raise UsageError(f"Required environment variable not set: {name}")
        return default

    return convert_type(value, type_, name)
