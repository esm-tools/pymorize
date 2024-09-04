import copy
import glob
import json
import re
from enum import Enum
from pathlib import Path
from typing import Union

from .frequency import CMIP_FREQUENCIES, Frequency
from .logging import logger


class IgnoreTableFiles(Enum):
    """Table files to ignore when reading from a directory."""

    CV_TEST = "CMIP6_CV_test.json"
    COORDINATE = "CMIP6_coordinate.json"
    CV = "CMIP6_CV.json"
    FORMULA_TERMS = "CMIP6_formula_terms.json"
    GRIDS = "CMIP6_grids.json"
    INPUT_EXAMPLE = "CMIP6_input_example.json"


class DataRequestVariable:
    """A variable in a particular DataRequest"""

    def __init__(
        self,
        variable_id,
        unit,
        description,
        time_method,
        table,
        frequency,
        realms,
        standard_name,
        cell_methods,
        cell_measures,
    ):
        self.variable_id = variable_id
        self.unit = unit
        self.description = description
        self.time_method = time_method
        self.tables = [table]
        self.frequencies = [frequency]
        self.realms = realms
        self.standard_name = standard_name
        self.cell_methods = [cell_methods]
        self.cell_measures = [cell_measures]

    @classmethod
    def from_table_var_entry(cls, var_entry):
        return cls(
            var_entry.variable_id,
            var_entry.unit,
            var_entry.description,
            var_entry.time_method,
            var_entry.table,
            var_entry.frequency_name,
            var_entry.realms,
            var_entry.standard_name,
            var_entry.cell_methods,
            var_entry.cell_measures,
        )

    def clone(self):
        return copy.deepcopy(self)

    def merge_table_var_entry(self, var_entry):
        # breakpoint()
        self.tables.append(var_entry.table)
        self.frequencies.append(var_entry.frequency_name)
        self.cell_methods.append(
            var_entry.cell_methods
        )  # some variables have different entries for cell_methods for different tables
        self.cell_measures.append(
            var_entry.cell_measures
        )  # some variables have different entries for cell_measures for different tables

    @property
    def table_ids(self) -> list[str]:
        return [t.table_id for t in self.tables]

    def frequency_in_table(self, table_id):
        try:
            i = self.table_ids().index(table_id)
        except ValueError:
            raise ValueError(
                f"variable_id '{self.variable_id}' is not associated with table_id '{table_id}', available table_id(s): {', '.join(self.table_ids)}"
            )
        return self.frequencies[i]

    def cell_methods_in_table(self, table_id):
        try:
            i = self.table_ids().index(table_id)
        except ValueError:
            raise ValueError(
                f"variable_id '{self.variable_id}' is not associated with table_id '{table_id}', available table_id(s): {', '.join(self.table_ids)}"
            )
        return self.cell_methods[i]

    def cell_measures_in_table(self, table_id):
        try:
            i = self.table_ids().index(table_id)
        except ValueError:
            raise ValueError(
                f"variable_id '{self.variable_id}' is not associated with table_id '{table_id}', available table_id(s): {', '.join(self.table_ids)}"
            )
        return self.cell_measures[i]

    def depluralize(self):
        self.table = self.tables[0]
        self.frequency = self.frequencies[0]
        self.cell_method = self.cell_methods[0]
        self.cell_measure = self.cell_measures[0]

    # def __iter__(self):
    #     yield DataRequestVariableStub.from_drv(self)

    def __str__(self):
        return f"{self.variable_id} '{self.unit}' [{' '.join(self.frequencies)}] [{' '.join([t.table_id for t in self.tables])}]"

    def __repr__(self):
        return f"""{self.__class__.__name__}(
                {self.variable_id},
                {self.unit},
                {self.description},
                {self.tables},
                {self.frequencies},
                {self.realms},
                {self.standard_name},
                {self.cell_methods},
                {self.cell_measures})"""


# class DataRequestVariableStub(DataRequestVariable):
#     @classmethod
#     def from_drv(cls, drv):
#         obj = cls(
#             drv.variable_id,
#             drv.unit,
#             drv.description,
#             drv.time_method,
#             drv.table,
#             drv.frequency,
#             drv.realms,
#             drv.standard_name,
#             drv.cell_method,
#             drv.cell_measure,
#         )
#         obj.depluralize()
#         return obj


class DataRequest:
    """Represents a data request with associated metadata."""

    # NOTE(PG): Inherited from Ruby Seamore, not needed for now.
    @staticmethod
    def approx_interval_for_table(table_id):
        return CMIP_FREQUENCIES[table_id]

    def __init__(self, paths: list[Union[str, Path]]):
        """
        Parameters
        ----------
        paths : list of str or Path
            Paths to the data request table files.
        """
        self.tables = [DataRequestTable(path) for path in paths]
        for x in self.tables:
            if self.tables[0].version != x.version:
                raise ValueError(
                    f"tables have different data request versions ({self.tables[0].version}@{self.tables[0].path} vs {x.version}@{x.path})"
                )
        self.tables = sorted(self.tables, key=lambda x: x.table_id)
        # Merge variables with identical variable_id and frequency which may appear in multiple tables
        _vars = []
        for t in self.tables:
            for var in t.variable_entries.values():
                _vars.append(var)
        _vars = sorted(
            _vars,
            key=lambda v: f"{v.variable_id} {v.unit} {v.time_method} {v.table.approx_interval} {v.table.table_id}",
        )

        merged_vars = []
        for v in _vars:
            matches = self._find_matching_var_for_merge(v, merged_vars)
            if matches:
                for mv in matches:
                    mv.merge_table_var_entry(v)
            else:
                merged_vars.append(DataRequestVariable.from_table_var_entry(v))

        self.variables = merged_vars

    @staticmethod
    def _find_matching_var_for_merge(
        v: DataRequestVariable, merged_vars: list[DataRequestVariable]
    ) -> list[DataRequestVariable]:
        condition_attrs = ["variable_id", "unit", "time_method"]
        matches = []
        for mv in merged_vars:
            if v.variable_id == mv.variable_id:
                if v.variable_id == "tos":
                    logger.debug("variable_id match")
                    # breakpoint()
            if all(getattr(v, attr) == getattr(mv, attr) for attr in condition_attrs):
                matches.append(mv)
        return matches

    @classmethod
    def from_tables_dir(cls, path):
        ignore_files = [f"{path}/{file.value}" for file in IgnoreTableFiles]
        eligible_files = glob.glob(f"{path}/CMIP6_*.json")
        eligible_files = [f for f in eligible_files if f not in ignore_files]

        if not eligible_files:
            raise ValueError(f"no eligible json tables found at path <{path}>")

        return cls(eligible_files)

    def find(self, variable_id, frequency_name):
        """
        This method finds a variable in the list of variables based on the variable_id and frequency_name.

        Parameters
        ----------
        variable_id : str
            The ID of the variable to find.
        frequency_name : str
            The name of the frequency to find.

        Returns
        -------
        The found variable, or None if no variable was found.
        """
        return next(
            (
                v
                for v in self.variables
                if variable_id == v.variable_id and frequency_name in v.frequencies
            ),
            None,
        )

    def find_variable_id_in_table_id(self, variable_id, table_id):
        """
        This method finds a variable in the list of variables based on the variable_id and table_id.

        Parameters
        ----------
        variable_id : str
            The ID of the variable to find.
        table_id : str
            The ID of the table to find.

        Returns
        -------
        The found variable, or None if no variable was found.
        """
        return next(
            (
                v
                for v in self.variables
                if variable_id == v.variable_id and table_id in v.table_ids
            ),
            None,
        )

    @property
    def variable_ids(self):
        """
        Returns
        -------
        list
            A list of variable IDs from the variables property.
        """
        return [v.variable_id for v in self.variables]

    @property
    def version(self):
        """
        Returns
        -------
        str
            The version of the first table in the tables property.
        """
        return self.tables[0].version

    @property
    def table_ids(self):
        """
        Returns
        -------
        list
            A list of table IDs from the tables property.
        """
        return [t.table_id for t in self.tables]

    def __str__(self):
        s = f"=== {self.version} ===\n"
        for v in self.variables:
            s += f"{v}\n"
        return s


class TableVarEntry:
    """Represents a variable entry in a data request table with associated metadata."""

    def __init__(self, variable_entry_key, variable_dict, table):
        self.variable_id = variable_entry_key
        self._data = variable_dict
        self.table = table
        self.frequency_name = self._data["frequency"]
        self.time_method = Frequency.for_name(self.frequency_name).time_method
        self.unit = self._data["units"]
        self.description = self._data["comment"]
        self.realms = self._data["modeling_realm"].split(" ")
        self.standard_name = self._data["standard_name"]
        self.cell_methods = self._data["cell_methods"]
        self.cell_measures = self._data["cell_measures"]


class DataRequestTable:
    """Represents a data request table with associated metadata."""

    def __init__(self, path: Union[str, Path] = None):
        """
        Parameters
        ----------
        path : str or Path
            Path to the data request table file.

        Raises
        ------
        ValueError
            If the data request file does not contain a Header section with mip_era or table_id.
        """
        self._path = path
        with open(path) as f:
            self._data = json.load(f)
        self._header_sanity_checks()
        self._assign_variable_entries()

        match = re.match(r"Table (?P<table_id>\w+)$", self._data["Header"]["table_id"])
        if not match:
            raise ValueError(f"Cannot determine table_id: <{path}>")
        self.table_id = match.group("table_id")

    def __repr__(self):
        return f"{self.__class__.__name__}({self._path})"

    def __str__(self):
        return f"{self.table_id} ({self.version}, loaded from {self._path})"

    def _header_sanity_checks(self):
        if "Header" not in self._data:
            raise ValueError("Data request file does not contain a Header section")
        if "table_id" not in self._data["Header"]:
            raise ValueError("Data request file does not contain a table_id")
        if "mip_era" not in self._data["Header"]:
            raise ValueError("Data request file does not contain a mip_era")

    def _assign_variable_entries(self):
        self._variable_entries = {}
        for variable_key, variable_dict in self._data["variable_entry"].items():
            self._variable_entries[variable_key] = TableVarEntry(
                variable_key, variable_dict, self
            )

    @property
    def frequencies(self):
        """Frequencies described by this data request table."""
        frequencies = []
        for variable_dict in self._data["variable_entry"].values():
            if "frequency" in variable_dict:
                frequencies.append(variable_dict["frequency"])
        return set(frequencies)

    @property
    def variable_ids(self):
        """Variable IDs in this data request table."""
        return sorted(list(self._data["variable_entry"].keys()))

    @property
    def variable_entries(self):
        return self._variable_entries

    @property
    def version(self):
        return self._data["Header"]["data_specs_version"]

    @property
    def approx_interval(self):
        """Approximate interval of the data request in days."""
        return self._data["Header"]["approx_interval"]
