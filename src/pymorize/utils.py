"""
Various utility functions needed around the package
"""

import inspect
from functools import partial

import pkg_resources
from loguru import logger


def get_callable_by_name(name):
    """
    Get a callable by its name.

    This function takes a string that represents the fully qualified name of a callable object
    (i.e., a function or a method), and returns the actual callable object. The name should be in
    the format 'module.submodule.callable'. If the callable does not exist, this function will raise
    an AttributeError.

    Parameters
    ----------
    name : str
        The fully qualified name of the callable to be retrieved. It should be in the format
        'module.submodule.callable'.

    Returns
    -------
    callable
        The callable object that corresponds to the given name.

    Raises
    ------
    ImportError
        If the module or submodule specified in the name does not exist.
    AttributeError
        If the callable specified in the name does not exist in the given module or submodule.
    """
    if "." not in name:
        raise ValueError(
            f"Name '{name}' is not a fully qualified name. It should be in the format 'module.submodule.callable'."
        )
    module_name, callable_name = name.rsplit(".", 1)
    logger.debug(f"Importing module '{module_name}' to get callable '{callable_name}'")
    module = __import__(module_name, fromlist=[callable_name])
    return getattr(module, callable_name)


def get_entrypoint_by_name(name, group="pymorize.rules"):
    """
    Get an entry point by its name.

    This function takes a string that represents the name of an entry point in a given group,
    and returns the actual entry point object. If the entry point does not exist, this function
    will raise a ValueError.

    Parameters
    ----------
    name : str
        The name of the entry point to be retrieved.

    group : str
        The group that the entry point belongs to.

    Returns
    -------
    EntryPoint
        The entry point object that corresponds to the given name.

    Raises
    ------
    ValueError
        If the entry point specified by the name does not exist in the given group.
    """
    logger.debug(f"Getting entry point '{name}' from group '{group}'")
    for entry_point in pkg_resources.iter_entry_points(group=group):
        if entry_point.name == name:
            return entry_point.load()

    raise ValueError(f"Entry point '{name}' not found in group '{group}'")


def generate_partial_function(func: callable, open_arg: str, *args, **kwargs):
    """
    Reduces func to a partial function by fixing all but the argument named by open_arg.

    Parameters
    ----------
    func : callable
        The function to be partially applied.
    open_arg : str
        The name of the argument that should remain open in the partial function.
    *args
        Positional arguments to be passed to the partial function.
    **kwargs
        Keyword arguments to be passed to the partial function.

    Returns
    -------
    callable
        The partial function with the specified arguments fixed.
    """
    if not can_be_partialized(func, open_arg, args, kwargs):
        raise ValueError(
            f"Function '{func.__name__}' cannot be partially applied with open argument '{open_arg}' by using the provided arguments {args=} and keyword arguments {kwargs=}."
        )
    logger.debug(
        f"Generating partial function for '{func.__name__}' with open argument '{open_arg}'"
    )
    # Get the signature of the function
    signature = inspect.signature(func)
    # Get the parameter names
    param_names = list(signature.parameters.keys())
    # Get the index of the open argument
    open_arg_index = param_names.index(open_arg)
    # Get the names of the arguments to be fixed
    fixed_args = param_names[:open_arg_index] + param_names[open_arg_index + 1 :]
    # Get the values of the arguments to be fixed
    fixed_values = [kwargs[arg] for arg in fixed_args if arg in kwargs]
    # Remove the fixed arguments from the keyword arguments
    for arg in fixed_args:
        kwargs.pop(arg, None)
    # Create the partial function
    return partial(func, *fixed_values, *args, **kwargs)


def can_be_partialized(
    func: callable, open_arg: str, arg_list: list, kwargs_dict: dict
) -> bool:
    """
    Checks if a function can be reasonably partialized with a single argument open.

    Parameters
    ----------
    func : callable
        The function to be partially applied.
    open_arg : str
        The name of the argument that should remain open in the partial function.
    arg_list : list
        The list of arguments that will be passed to the partial function.
    kwargs_dict : dict
        The dictionary of keyword arguments that will be passed to the partial function.

    Returns
    -------
    bool
        True if the function can be partially applied with a single argument open, False otherwise.
    """
    signature = inspect.signature(func)
    param_names = list(signature.parameters.keys())
    # Check that all arguments in arg_list are in the function signature
    for arg in arg_list:
        if arg in param_names:
            param_names.remove(arg)
    for kwarg in kwargs_dict:
        if kwarg in param_names:
            param_names.remove(kwarg)
    # Check that there is only one argument left and that it is open_arg
    return len(param_names) == 1 and param_names[0] == open_arg
