"""
Functionality for gathering possible inputs from a user directory
"""

import os
import pathlib
import re
from typing import List

import dpath
import yaml

_PATTERN_ENV_VAR_NAME_ADDR = "/pymorize/pattern_env_var_name"
"""str: The address in the YAML file which stores the environment variable to be used for the pattern"""
_PATTERN_ENV_VAR_NAME_DEFAULT = "PYMORIZE_INPUT_PATTERN"
"""str: The default value for the environment variable to be used for the pattern"""
_PATTERN_ENV_VAR_VALUE_ADDR = "/pymorize/pattern_env_var_value"
"""str: The address in the YAML file which stores the environment variable's value to be used if the variable is not set"""
_PATTERN_ENV_VAR_VALUE_DEFAULT = ".*"  # Default: match anything
"""str: The default value for the environment variable's value to be used if the variable is not set"""


def _input_pattern_from_env(config: dict) -> re.Pattern:
    """
    Get the input pattern from the environment variable.

    This function retrieves the name of the environment variable from the configuration dictionary
    using the dpath library. It then gets the value of this environment variable, which is expected
    to be a regular expression pattern. This pattern is then compiled and returned.

    Parameters
    ----------
    config : dict
        The configuration dictionary. This dictionary should contain the keys
        `pattern_env_var_name` and `pattern_env_value_default`, which are used to locate
        the environment variable name and default value respectively. If not gives, these default
        to `PYMORIZE_INPUT_PATTERN` and `.*` respectively.

    Returns
    -------
    re.Pattern
        The compiled regular expression pattern.

    Examples
    --------
    >>> config_bare = { "pymorize": {} }
    >>> config_only_env_name = {
    ...     "pymorize": {
    ...         'pattern_env_var_name': 'CMOR_PATTERN',
    ...     }
    ... }
    >>> config_only_env_value = {
    ...     "pymorize": {
    ...         'pattern_env_var_default': 'test*nc',
    ...   }
    ... }
    >>> pattern = _input_pattern_from_env(config_bare)
    >>> pattern
    re.compile('.*')
    >>> bool(pattern.match('test'))
    True
    >>> pattern = _input_pattern_from_env(config_only_env_name)
    >>> os.environ["CMOR_PATTERN"] = "test*nc"
    >>> pattern
    re.compile('test*nc')
    >>> bool(pattern.match('test'))
    True
    >>> pattern = _input_pattern_from_env(config_only_env_value)
    >>> pattern
    re.compile('.*')
    >>> bool(pattern.match('test'))
    True
    """
    env_var_name = dpath.get(
        config, _PATTERN_ENV_VAR_NAME_ADDR, default=_PATTERN_ENV_VAR_NAME_DEFAULT
    )
    env_var_value = os.getenv(
        env_var_name,
        dpath.get(
            config, _PATTERN_ENV_VAR_VALUE_ADDR, default=_PATTERN_ENV_VAR_VALUE_DEFAULT
        ),
    )
    return re.compile(env_var_value)


def input_files_in_path(path: pathlib.Path or str, pattern: re.Pattern) -> list:
    """
    Get a list of files in a directory that match a pattern.

    This function takes a directory path and a regular expression pattern. It then
    returns a list of all files in the directory that match the pattern.

    Parameters
    ----------
    path : pathlib.Path or str
        The path to the directory to search for files.

    pattern : re.Pattern

    Returns
    -------
    list
        A list of files in the directory that match the pattern.
    """
    path = pathlib.Path(path)
    return [f for f in path.iterdir() if f.is_file() and pattern.match(f.name)]


def resolve_symlinks(files: List[pathlib.Path]) -> List[pathlib.Path]:
    """
    Filters out symbolic links from a list of pathlib.Path objects.

    Parameters
    ----------
    files : list
        A list of pathlib.Path objects.

    Returns
    -------
    list
        A list of pathlib.Path objects excluding any symbolic links.

    Raises
    ------
    TypeError
        If any element in the input list is not a pathlib.Path object.

    Examples
    --------
    >>> from pathlib import Path
    >>> files = [Path('/path/to/file1'), Path('/path/to/file2')]
    >>> resolve_symlinks(files)
    [Path('/path/to/file1'), Path('/path/to/file2')]
    """
    if not all(isinstance(f, pathlib.Path) for f in files):
        raise TypeError("All files must be pathlib.Path objects")
    return [f.resolve() if f.is_symlink() else f for f in files]
