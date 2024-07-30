import re

import questionary
import yaml
from loguru import logger


class Rule:
    """
    A Rule is a set of instructions to process a file and convert it to a CMOR standard.

    Parameters
    ----------
    input_pattern : str or list of str
    cmor_variable : str
    pipelines : list of pipelines to be applied to files described by this rule
    """

    def __init__(self, input_pattern, cmor_variable):
        """
        Parameters
        ----------
        input_pattern : str or list of str
            A regular expression pattern to match the input file path.
        cmor_variable : str
            The CMOR variable name.
        """
        if isinstance(input_pattern, str):
            self.input_patterns = list(re.compile(input_pattern))
        elif isinstance(input_pattern, list):
            self.input_patterns = [re.compile(str(p)) for p in input_pattern]
        else:
            raise TypeError("input_pattern must be a string or a list of strings")
        self.cmor_variable = cmor_variable

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

    @classmethod
    def from_dict(cls, data):
        input_patterns = [re.compile(p) for p in data["input_patterns"]]
        cmor_variable = data["cmor_variable"]
        return cls(input_patterns, cmor_variable)

    def to_yaml(self):
        return yaml.dump(
            {
                "input_patterns": [p.pattern for p in self.input_patterns],
                "cmor_variable": self.cmor_variable,
            }
        )
