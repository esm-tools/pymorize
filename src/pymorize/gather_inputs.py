"""
Functionality for gathering possible inputs from a user directory
"""

import os
import pathlib
import re
from typing import List

import dpath

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


def _input_files_in_path(path: pathlib.Path or str, pattern: re.Pattern) -> list:
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


def _resolve_symlinks(files: List[pathlib.Path]) -> List[pathlib.Path]:
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
    >>> _resolve_symlinks(files)
    [Path('/path/to/file1'), Path('/path/to/file2')]
    """
    if not all(isinstance(f, pathlib.Path) for f in files):
        raise TypeError("All files must be pathlib.Path objects")
    return [f.resolve() if f.is_symlink() else f for f in files]


def _filter_by_year(
    files: List[pathlib.Path], fpattern: re.Pattern, year_start: int, year_end: int
) -> List[pathlib.Path]:
    """
    Filters a list of files by the year in their name.
    """
    return [
        f
        for f in files
        if year_start <= int(fpattern.match(f.name).group("year")) <= year_end
    ]


def _sort_by_year(
    files: List[pathlib.Path], fpattern: re.Pattern
) -> List[pathlib.Path]:
    """
    Sorts a list of files by the year in their name.
    """
    return sorted(files, key=lambda f: int(fpattern.match(f.name).group("year")))


def _files_to_string(files: List[pathlib.Path], sep=",") -> str:
    """
    Converts a list of pathlib.Path objects to a string.

    Parameters
    ----------
    files : list
        A list of pathlib.Path objects.
    sep : str
        The separator to use between the paths. Defaults to a comma.

    Returns
    -------
    str
        A string representation of the list of files.
    """
    return sep.join(str(f) for f in files)


def _validate_rule_has_marked_regex(
    rule: dict, required_marks: List[str] = ["year"]
) -> bool:
    """
    Validates that a rule has a marked regular expression.

    This function takes a rule dictionary and a list of required marks. It then checks that
    the rule has a regular expression pattern that has been marked with all of the required marks.

    Parameters
    ----------
    rule : dict
        The rule dictionary.
    required_marks : list
        A list of strings representing the required marks.

    Returns
    -------
    bool
        True if the rule has a marked regular expression, False otherwise.

    Examples
    --------
    >>> rule = { 'pattern': 'test(?P<year>[0-9]{4})' }
    >>> _validate_rule_has_marked_regex(rule)
    True
    >>> rule = { 'pattern': 'test' }
    >>> _validate_rule_has_marked_regex(rule)
    False
    """
    pattern = rule.get("pattern")
    if pattern is None:
        return False
    return all(re.search(rf"\(\?P<{mark}>", pattern) for mark in required_marks)


def gather_inputs(config: dict) -> dict:
    """
    Gather possible inputs from a user directory.

    This function takes a configuration dictionary and returns a list of pathlib.Path objects
    representing the files in the directory that match the pattern specified in the configuration.

    Parameters
    ----------
    config : dict
        The configuration dictionary. This dictionary should contain the keys
        `pattern_env_var_name` and `pattern_env_value_default`, which are used to locate
        the environment variable name and default value respectively. If not gives, these default
        to `PYMORIZE_INPUT_PATTERN` and `.*` respectively.

    Returns
    -------
    config:
        The configuration dictionary with the input files added.


    Examples
    --------
    Assuming a filesystem with::

        /path/to/input/files/test2000.nc
        /path/to/input/files/test2001.nc
        /path/to/input/files/test2002.nc
        /path/to/input/files/test2003.nc
        /path/to/input/files/test2004.nc
        /path/to/input/files/test2005.nc
        /path/to/input/files/test2006.nc
        /path/to/input/files/test2007.nc
        /path/to/input/files/test2008.nc
        /path/to/input/files/test2009.nc
        /path/to/input/files/test2010.nc

    >>> config = {
    ...     "rules": [
    ...         {
    ...             "input_patterns": [
    ...                 "/path/to/input/files/test*nc"
    ...             ],
    ...             "year_start": 2000,
    ...             "year_end": 2010
    ...         }
    ...     ]
    ... }
    >>> gather_inputs(config)
    {
        "rules": [
            {
                "input_patterns": [
                    "/path/to/input/files/test*nc"
                ],
                "year_start": 2000,
                "year_end": 2010,
                "input_files": {
                    "/path/to/input/files/test*nc": [
                        "/path/to/input/files/test2000.nc",
                        "/path/to/input/files/test2001.nc",
                        "/path/to/input/files/test2002.nc",
                        "/path/to/input/files/test2003.nc",
                        "/path/to/input/files/test2004.nc",
                        "/path/to/input/files/test2005.nc",
                        "/path/to/input/files/test2006.nc",
                        "/path/to/input/files/test2007.nc",
                        "/path/to/input/files/test2008.nc",
                        "/path/to/input/files/test2009.nc",
                        "/path/to/input/files/test2010.nc"
                    ],
                 }
            }
        ]
    }
    """
    rules = config.get("rules", [])
    for rule in rules:
        input_patterns = rule.get("input_patterns", [])
        input_files = {}
        year_start = rule.get("year_start")
        year_end = rule.get("year_end")
        if year_start is not None:
            year_start = int(year_start)
        if year_end is not None:
            year_end = int(year_end)
        for input_pattern in input_patterns:
            if _validate_rule_has_marked_regex(input_pattern):
                pattern = re.compile(input_pattern["pattern"])
            else:
                # FIXME(PG): This needs to be thought through...
                # If the pattern is not marked, use the environment variable
                pattern = _input_pattern_from_env(config)
            files = _input_files_in_path(input_pattern["path"], pattern)
            files = _resolve_symlinks(files)
            if year_start is not None and year_end is not None:
                files = _filter_by_year(files, pattern, year_start, year_end)
                files = _sort_by_year(files, pattern, year_start, year_end)
            input_files[input_pattern] = files
        rule["input_files"] = input_files
    return config