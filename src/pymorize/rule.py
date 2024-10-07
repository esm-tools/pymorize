import copy
import re
import typing
import warnings
from collections import OrderedDict

# import questionary
import yaml

from . import data_request, pipeline
from .gather_inputs import InputFileCollection
from .logging import logger


class Rule:
    def __init__(
        self,
        *,
        inputs: typing.List[dict] = [],
        cmor_variable: str,
        pipelines: typing.List[pipeline.Pipeline] = [],
        tables: typing.List[data_request.DataRequestTable] = [],
        data_request_variables: typing.List[data_request.DataRequestVariable] = [],
        **kwargs,
    ):
        """
        Initialize a Rule object.

        This method can only be called with keyword arguments.

        Parameters
        ----------
        inputs : list of dicts for InputFileCollection
            Dictionaries should contain the keys "path" and "pattern".
        cmor_variable : str
            The CMOR variable name. This is the name of the variable as it should appear in the CMIP archive.
        pipelines : list of Pipeline objects
            A list of Pipeline objects that define the transformations to be applied to the data.
        tables : list of DataRequestTable objects
            A list of data request tables associated with this rule
        data_request_variables : DataRequestVariable or None :
            The DataRequestVariables this rule should create
        """
        self.inputs = [InputFileCollection.from_dict(inp_dict) for inp_dict in inputs]
        self.cmor_variable = cmor_variable
        self.pipelines = pipelines or [pipeline.DefaultPipeline()]
        self.tables = tables
        self.data_request_variables = data_request_variables
        # NOTE(PG): I'm not sure I really like this part. It is too magical and makes the object's public API unclear.
        # Attach all keyword arguments to the object
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Internal flags:
        self._pipelines_are_mapped = False

    def get(self, key, default=None):
        return getattr(self, key, default)

    def set(self, key, value, force=False, warn=True):
        """
        Set a new attribute for the object.

        Parameters
        ----------
        key : str
            The name of the attribute to set.
        value : Any
            The value to set for the attribute.
        force : bool, optional
            If True, the attribute will be overwritten if it already exists.
            If False (default), an AttributeError will be raised if the attribute already exists.
        warn : bool, optional
            If True (default) a warning will be issued if the attribute already exists, and
            it will not be overwritten. If False, an AttributeError will be raised if the attribute
            already exists.

        Returns
        -------
        value : Any
            Returns the value appended to the object. This is the same behaviour as setattr.

        Raises
        ------
        AttributeError
            If the attribute already exists and force and warn are both False.
        """
        if hasattr(self, key) and not force:
            if warn:
                warnings.warn(
                    f"Attribute {key} already exists. Use force=True to overwrite."
                )
            else:
                raise AttributeError(
                    f"Attribute {key} already exists. Use force=True to overwrite."
                )
        return setattr(self, key, value)

    def __repr__(self):
        return f"Rule(inputs={self.inputs}, cmor_variable={self.cmor_variable}, pipelines={self.pipelines}, tables={self.tables}, data_request_variables={self.data_request_variables})"

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
            logger.debug("Pipelines already mapped, nothing to do")
            return self.pipelines
        known_pipelines = {p.name: p for p in pipelines}
        logger.debug("The following pipelines are known:")
        for pl_name, pl in known_pipelines.items():
            logger.debug(f"{pl_name}: {pl}")
        matched_pipelines = list()
        for pl in self.pipelines:
            logger.debug(f"Working on: {pl}")
            # Pipeline was already matched
            if isinstance(pl, pipeline.Pipeline):
                matched_pipelines.append(pl)
            elif isinstance(pl, str):
                # Pipeline name:
                matched_pipelines.append(known_pipelines[pl])
            else:
                logger.error(f"No known way to match the pipeline {pl}")
                raise TypeError(f"{pl} must be a string or a pipeline.Pipeline object!")
        self.pipelines = matched_pipelines
        self._pipelines_are_mapped = True

    @classmethod
    def from_dict(cls, data):
        return cls(
            inputs=data.pop("inputs"),
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
                "inputs": [p.to_dict for p in self.input_patterns],
                "cmor_variable": self.cmor_variable,
                "pipelines": [p.to_dict() for p in self.pipelines],
            }
        )

    def add_table(self, tbl):
        self.tables.append(tbl)
        self.tables = [t for t in self.tables if t is not None]

    def add_data_request_variable(self, drv):
        self.data_request_variables.append(drv)
        # Filter out Nones
        self.data_request_variables = [
            v for v in self.data_request_variable if v is not None
        ]

    @property
    def input_patterns(self):
        deprecated = "input_patterns is deprecated. Use inputs instead."
        warnings.warn(deprecated, DeprecationWarning)
        return [re.compile(f"{inp.path}/{inp.pattern}") for inp in self.inputs]

    def clone(self):
        return copy.deepcopy(self)

    def expand_drvs(self):
        clones = []
        for drv in self.data_request_variables:
            rule_clone = self.clone()
            drv_clone = drv.clone()
            for drv_table, drv_freq, cell_methods, cell_measures in zip(
                drv.tables, drv.frequencies, drv.cell_methods, drv.cell_measures
            ):
                drv_clone.tables = [drv_table]
                drv_clone.frequencies = [drv_freq]
                drv_clone.cell_methods = [cell_methods]
                drv_clone.cell_measures = [cell_measures]
                rule_clone.data_request_variables = [drv_clone]
                clones.append(rule_clone)
        return clones

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
