import re
from functools import partial

import questionary
import yaml
from loguru import logger

from .generic import set_cmor_metadata
from .utils import generate_partial_function, get_callable_by_name


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
