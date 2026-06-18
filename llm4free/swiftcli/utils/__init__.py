"""Utility functions for SwiftCLI."""

from .formatting import (
    clear_screen,
    create_padding,
    create_table,
    format_dict,
    format_error,
    format_info,
    format_list,
    format_success,
    format_warning,
    get_terminal_size,
    strip_ansi,
    style_text,
    truncate_text,
    wrap_text,
)
from .parsing import (
    convert_type,
    get_env_var,
    load_config_file,
    parse_args,
    parse_dict,
    parse_key_value,
    parse_list,
    validate_choice,
    validate_required,
)

__all__ = [
    # Formatting utilities
    'style_text',
    'format_error',
    'format_warning',
    'format_success',
    'format_info',
    'create_table',
    'truncate_text',
    'wrap_text',
    'format_dict',
    'format_list',
    'strip_ansi',
    'get_terminal_size',
    'clear_screen',
    'create_padding',

    # Parsing utilities
    'parse_args',
    'validate_required',
    'convert_type',
    'validate_choice',
    'load_config_file',
    'parse_key_value',
    'parse_list',
    'parse_dict',
    'get_env_var'
]
