import re
import typing
from collections import OrderedDict

# import questionary
import yaml

from . import pipeline
from .logging import logger


class Rule:
    def __init__(
        self,
        *,
        input_patterns: typing.Union[str, typing.List[str]],
        cmor_variable: str,
        pipelines: typing.List[pipeline.Pipeline] = [],
        tables = [],
        **kwargs,
    ):
        """
        Initialize a Rule object.

        This method can only be called with keyword arguments.

        Parameters
        ----------
        input_pattern : str or list of str
            A regular expression pattern or a list of patterns to match the input file path.
        cmor_variable : str
            The CMOR variable name. This is the name of the variable as it should appear in the CMIP archive.
        pipelines : list of Pipeline objects
            A list of Pipeline objects that define the transformations to be applied to the data.

        Raises
        ------
        TypeError
            If input_pattern is not a string or a list of strings.
        """
        if isinstance(input_patterns, str):
            self.input_patterns = list(re.compile(input_patterns))
        elif isinstance(input_patterns, list):
            self.input_patterns = [re.compile(str(p)) for p in input_patterns]
        else:
            raise TypeError("input_pattern must be a string or a list of strings")

        self.cmor_variable = cmor_variable
        self.pipelines = pipelines or [pipeline.DefaultPipeline()]
        self.tables = tables
        # NOTE(PG): I'm not sure I really like this part. It is too magical and makes the object's public API unclear.
        # Attach all keyword arguments to the object
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Internal flags:
        self._pipelines_are_mapped = False

    def __repr__(self):
        return f"Rule(input_patterns={self.input_patterns}, cmor_variable={self.cmor_variable}, pipelines={self.pipelines})"

    def __str__(self):
        return f"Rule for {self.cmor_variable} with input patterns {self.input_patterns} and pipelines {self.pipelines}"

    def match_pipelines(self, pipelines, force=False):
        """
        Match the pipelines in the rule with the pipelines in the configuration. The pipelines
        should be a list of pipeline instances that can be matched with the rule's required pipelines.

        Parameters
        ----------
        list : list of pipeline.Pipeline
            Available pipelines to use
        force : bool, optional
            If True, the pipelines will be remapped even if they were already mapped.

        Mutates
        -------
        self.pipelines : list of str --> list of pipeline.Pipeline objects
            ``self.pipelines`` will be replaced from a list of strings to a list of
            Pipeline objects. The order of the pipelines will be preserved.
        """
        if self._pipelines_are_mapped and not force:
            return self.pipelines
        known_pipelines = {p.name: p for p in pipelines}
        matched_pipelines = OrderedDict()
        for pl in self.pipelines:
            # Pipeline was already matched
            if isinstance(pl, pipeline.Pipeline):
                continue
            # Pipeline name:
            matched_pipelines[pl] = known_pipelines[pl]
        self.pipelines = list(matched_pipelines.values())

    @classmethod
    def from_dict(cls, data):
        return cls(
            input_patterns=data.pop("input_patterns"),
            cmor_variable=data.pop("cmor_variable"),
            pipelines=data.pop("pipelines", []),
            **data,
        )

    @classmethod
    def from_yaml(cls, yaml_str):
        return cls.from_dict(yaml.safe_load(yaml_str))

    def to_yaml(self):
        return yaml.dump(
            {
                "input_patterns": [p.pattern for p in self.input_patterns],
                "cmor_variable": self.cmor_variable,
                "pipelines": [p.to_dict() for p in self.pipelines],
            }
        )

    def add_table(self, tbl):
        self.tables.append(tbl)

    # FIXME: Not used and broken+
    # @classmethod
    # def from_interface(cls, cmor_table=None):
    #     """
    #     Generates a Rule via a wizard-like interface

    #     Parameters
    #     ----------
    #     cmor_table : dict, optional
    #         A dictionary with the CMOR table. If provided, the user will be
    #         prompted to select a CMOR variable from the table. Must contain a key
    #         "variable_entry" with an iterable of CMOR variable names.
    #     """
    #     if cmor_table is None:
    #         cmor_variable = questionary.text("CMOR variable: ").ask()
    #     else:
    #         cmor_variable = questionary.autocomplete(
    #             "CMOR variable: ", cmor_table["variable_entry"]
    #         ).ask()
    #     input_patterns = []
    #     while True:
    #         input_patterns.append(questionary.text("Input pattern as regex: ").ask())
    #         if input_patterns:
    #             [logger.info(p) for p in input_patterns]
    #         if not questionary.confirm(
    #             f"Add another input pattern for {cmor_variable}?"
    #         ).ask():
    #             break
    #     return cls(input_patterns=input_patterns, cmor_variable=cmor_variable)
