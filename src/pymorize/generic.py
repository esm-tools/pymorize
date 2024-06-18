"""
This module, `generic.py`, provides functionalities for transforming and standardizing NetCDF files
according to CMOR.

It contains several functions and classes:

Functions (can be used as actions in `Rule` objects):
- `linear_transform`: Applies a linear transformation to the data of a NetCDF file.
- `invert_z_axis`: Inverts the z-axis of a NetCDF file.

Classes:
- `Rule`: Defines a set of instructions to process a file and convert it to a CMOR standard.
- `CMORMetadata`: Inherits from `Rule` and adds CMOR metadata to a NetCDF file.
- `CMORizer`: Manages a set of `Rule` objects and applies them to NetCDF files.

Each `Rule` object represents a set of transformations that should be applied to a NetCDF file to
make it comply with the CMOR standard. The `CMORizer` class manages a collection of `Rule` objects and
applies the appropriate ones to each file.

The `CMORMetadata` class is a special type of `Rule` that adds CMOR metadata to a file.

The Full CMOR (yes, bad pun):
    * Applied if no other rule sets are given for a file
    * Adds CMOR metadata to the file
    * Converts units
    * Performs time averaging
"""

import datetime
import json
import re
import sys
from functools import partial
from pathlib import Path

import questionary
import xarray as xr
import yaml
from loguru import logger

from .utils import generate_partial_function, get_callable_by_name


def convert_units(filepath: Path, source_units: str, target_units: str):
    """
    Converts the units of a NetCDF file, using the Pint library.

    Parameters
    ----------
    filepath : Path
        Path to the input file.
    source_units : str
    target_units : str
    """
    ds = xr.open_dataset(filepath)
    ds = ds.pint.quantify()
    ds = ds.pint.to(target_units)
    ds = ds.pint.dequantify()
    logger.info(f"Converted units of {filepath} from {source_units} to {target_units}")
    ds.to_netcdf(filepath)


def set_cmor_metadata(filepath: Path, cmor_metadata: dict, attrs_to_skip=[]):
    """
    Adds CMOR metadata to a NetCDF file.

    Parameters
    ----------
    filepath : Path
        Path to the input file.
    cmor_metadata : dict
        Dictionary with the CMOR metadata to be added to the file.
    attrs_to_skip : list of str, optional
        List of attributes to skip when adding CMOR metadata.
    """
    attrs_to_skip = attrs_to_skip or ["units", "cell_methods", "cell_measures"]
    ds = xr.open_dataset(filepath)
    for key, value in cmor_metadata.items():
        if key in attrs_to_skip:
            continue
        ds.attrs[key] = value
    hist_str = ds.attrs.get("history", "")
    hist_str += f"\n{datetime.now()}: CMOR metadata added by ``pymorize``\n"
    ds.to_netcdf(filepath)


def linear_transform(
    filepath: Path, execute: bool = False, slope: float = 1, offset: float = 0
):
    """
    Applies a linear transformation to the data of a NetCDF file.

    Parameters
    ----------
    filepath : Path
        Path to the input file.
    execute : bool, optional
    slope: float, optional
    offset: float, optional
    """
    if execute:
        ds = xr.open_dataset(filepath)
        ds = ds * slope + offset
        logger.info(f"Applied linear transformation to {filepath}")
        ds.to_netcdf(filepath)
    else:
        logger.info(f"Would apply linear transformation to {filepath}")
        logger.info(f"slope: {slope}, offset: {offset}")
        logger.info("Use `execute=True` to apply changes")


def invert_z_axis(filepath: Path, execute: bool = False, flip_sign: bool = False):
    """
    Inverts the z-axis of a NetCDF file.

    Parameters
    ----------
    filepath : Path
        Path to the input file.
    execute : bool, optional
        If True, the function will execute the inversion. If False, it will
        only print the changes that would be made.
    """
    if execute:
        ds = xr.open_dataset(filepath)
        ds = ds.reindex(z=ds.z[::-1])
        logger.info(f"Inverted order of z-axis of {filepath}")
        if flip_sign:
            ds["z"] *= -1
            logger.info(f"Flipped sign of z-axis of {filepath}")
        ds.to_netcdf(filepath)
    else:
        logger.info(f"Would invert z-axis of {filepath}")
        if flip_sign:
            logger.info("Would flip sign of z-axis")
        logger.info("Use `execute=True` to apply changes")


class Rule:
    """
    A Rule is a set of instructions to process a file and convert it to a CMOR standard.

    This class can be used to define a set of actions to be performed on a file. I

    Parameters
    ----------
    input_pattern : str or list of str
    cmor_variable : str
    actions : list of Callables, optional
    """

    def __init__(self, input_pattern, cmor_variable, actions=None):
        """
        Parameters
        ----------
        input_pattern : str or list of str
            A regular expression pattern to match the input file path.
        cmor_variable : str
            The CMOR variable name.
        actions : list of Callables, optional
            A list of functions to be called on the input file. Each function
            should have the signature `f(input_file: Path) -> None`.
        """
        if isinstance(input_pattern, str):
            self.input_patterns = list(re.compile(input_pattern))
        elif isinstance(input_pattern, list):
            self.input_patterns = [re.compile(p) for p in input_pattern]
        else:
            raise TypeError("input_pattern must be a string or a list of strings")
        self.cmor_variable = cmor_variable
        self.actions = actions or []

    @classmethod
    def from_interface(cls, cmor_table=None):
        """
        Generates a Rule via a wizard-like interface

        Parameters
        ----------
        cmor_table : dict, optional
            A dictionary with the CMOR table. If provided, the user will be
            prompted to select a CMOR variable from the table. Must contain a key
            "variable_entry" with an iterable of CMOR variable names.
        """
        if cmor_table is None:
            cmor_variable = questionary.text("CMOR variable: ").ask()
        else:
            cmor_variable = questionary.autocomplete(
                "CMOR variable: ", cmor_table["variable_entry"]
            ).ask()
        input_patterns = []
        while True:
            input_patterns.append(questionary.text("Input pattern as regex: ").ask())
            if input_patterns:
                [logger.info(p) for p in input_patterns]
            if not questionary.confirm(
                f"Add another input pattern for {cmor_variable}?"
            ).ask():
                break
        return cls(input_patterns, cmor_variable)

    @classmethod
    def from_yaml(cls, yaml_str):
        return cls.from_dict(yaml.safe_load(yaml_str))

    @staticmethod
    def _actions_from_dict(data):
        """Creates partially applied functions from a list of dicts"""
        actions = []
        for action_dict in data:
            for name, spec in action_dict.items():
                action = get_callable_by_name(name)
                if spec is None:
                    spec = dict()  # Empty dict, as partial needs a dict
                actions.append(partial(action, **spec))
        return actions

    @classmethod
    def from_dict(cls, data):
        input_patterns = [re.compile(p) for p in data["input_patterns"]]
        cmor_variable = data["cmor_variable"]
        # Convert action names to functions, which are partially applied with
        # the arguments provided in the dict
        actions = cls._actions_from_dict(data.get("actions", [{}]))
        return cls(input_patterns, cmor_variable, actions)

    def to_yaml(self):
        return yaml.dump(
            {
                "input_patterns": [p.pattern for p in self.input_patterns],
                "cmor_variable": self.cmor_variable,
                "actions": [a.__name__ for a in self.actions],
            }
        )


class CMORMetadata(Rule):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = [set_cmor_metadata]


class CMORizer:

    def __init__(self, cmor_table_dir, output_dir):
        self.cmor_table_dir = cmor_table_dir
        self.output_dir = output_dir

        self._rules = []

    @classmethod
    def from_yaml(cls, yaml_str):
        data = yaml.safe_load(yaml_str)
        instance = cls(data["cmor_table_dir"], data["output_dir"])
        for rule in data.get("rules", []):
            instance.add_rule(Rule.from_dict(rule))

    def add_rule(self, rule):
        if not isinstance(rule, Rule):
            raise TypeError("rule must be an instance of Rule")
        self._rules.append(rule)

    def _rule_for_filepath(self, filepath):
        matching_rules = []
        for rule in self._rules:
            for pattern in rule.input_patterns:
                if pattern.match(filepath):
                    matching_rules.append(rule)
        return matching_rules

    def _rule_for_cmor_variable(self, cmor_variable):
        for rule in self._rules:
            if rule.cmor_variable == cmor_variable:
                return rule
        return None

    def _check_rules_for_table(self):
        missing_variables = []
        for cmor_variable in self.cmor_table["variable_entry"]:
            if self._rule_for_cmor_variable(cmor_variable) is None:
                logger.warning(f"No rule found for {cmor_variable}")
                missing_variables.append(cmor_variable)
        if missing_variables:
            logger.warning("This CMORizer may be incomplete or badly configured!")
            logger.warning(
                f"Missing rules for >> {len(missing_variables)} << variables."
            )

    def _check_rules_for_output_dir(self):
        all_files_in_output_dir = [f for f in Path(self.output_dir).iterdir()]
        for rule in self._rules:
            # Remove files from list when matching a rule
            for filepath in all_files_in_output_dir:
                if self._rule_for_filepath(filepath):
                    all_files_in_output_dir.remove(filepath)
        if all_files_in_output_dir:
            logger.warning("This CMORizer may be incomplete or badly configured!")
            logger.warning(
                f"Found >> {len(all_files_in_output_dir)} << files in output dir not matching any rule."
            )
            if questionary.ask("Do you want to view these files?").ask():
                for filepath in all_files_in_output_dir:
                    logger.warning(filepath)

    def __call__(self, filepath):
        rule = self._rule_for_filepath(filepath)
        if rule is None:
            logger.warning(f"No rule found for {filepath}")
            continue_anyway = questionary.confirm("Continue anyway? ").ask()
            if continue_anyway:
                logger.info(f"Skipping {filepath} as no rule was found")
            else:
                logger.error(f"Aborting, as no rule was found for {filepath}")
                sys.exit(1)
        else:
            for action in rule.actions:
                action(filepath)
