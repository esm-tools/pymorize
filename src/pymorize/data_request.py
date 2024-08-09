import glob
import json
import re
from pathlib import Path
from typing import Union


class DataRequest:
    """Represents a data request with associated metadata."""

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
        vars = [var for t in self.tables for var in t.variable_entries]
        merged_vars = []
        vars = sorted(
            vars,
            key=lambda v: f"{v.variable_id} {v.unit} {v.time_method} {v.table.approx_interval} {v.table.table_id}",
        )

        for v in vars:
            if (
                merged_vars
                and merged_vars[-1].variable_id == v.variable_id
                and merged_vars[-1].unit == v.unit
                and merged_vars[-1].time_method == v.time_method
            ):
                merged_vars[-1].merge_table_var_entry(v)
            else:
                merged_vars.append(DataRequestVariable.new_from_table_var_entry(v))

        self.variables = merged_vars

    @classmethod
    def new_from_tables_dir(cls, path):
        eligible_files = glob.glob(f"{path}/CMIP6_*.json")
        exclude_files = [
            f"{path}/CMIP6_CV_test.json",
            f"{path}/CMIP6_coordinate.json",
            f"{path}/CMIP6_CV.json",
            f"{path}/CMIP6_formula_terms.json",
            f"{path}/CMIP6_grids.json",
            f"{path}/CMIP6_input_example.json",
        ]
        eligible_files = [file for file in eligible_files if file not in exclude_files]

        if not eligible_files:
            raise ValueError(f"no eligible json tables found at path <{path}>")

        return cls(eligible_files)

    def find(self, variable_id, frequency_name):
        return next(
            (
                v
                for v in self.variables
                if variable_id == v.variable_id and frequency_name in v.frequencies
            ),
            None,
        )

    def find_variable_id_in_table_id(self, variable_id, table_id):
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
        return [v.variable_id for v in self.variables]

    @property
    def version(self):
        return self.tables[0].version

    @property
    def table_ids(self):
        return [table_id for t in self.tables for table_id in t.table_id]

    def __str__(self):
        s = f"=== {self.version} ===\n"
        for v in self.variables:
            s += f"{v}\n"
        return s


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
        self.cell_methods_list = [cell_methods]
        self.cell_measures_list = [cell_measures]

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

    def merge_table_var_entry(self, var_entry):
        self.tables.append(var_entry.table)
        self.frequencies.append(var_entry.frequency_name)
        self.cell_methods_list.append(
            var_entry.cell_methods
        )  # some variables have different entries for cell_methods for different tables
        self.cell_measures_list.append(
            var_entry.cell_measures
        )  # some variables have different entries for cell_measures for different tables
        # we do not merge time methods, as we treat identical variable_ids with different time methods as different variables

    @property
    def table_ids(self):
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
        return self.cell_methods_list[i]

    def cell_measures_in_table(self, table_id):
        try:
            i = self.table_ids().index(table_id)
        except ValueError:
            raise ValueError(
                f"variable_id '{self.variable_id}' is not associated with table_id '{table_id}', available table_id(s): {', '.join(self.table_ids)}"
            )
        return self.cell_measures_list[i]

    def __str__(self):
        return f"{self.variable_id} '{self.unit}' [{' '.join(self.frequencies)}] [{' '.join([t.table_id for t in self.tables])}]"


class TableVarEntry:
    """Represents a variable entry in a data request table with associated metadata."""

    def __init__(self, variable_entry_key, variable_dict, table):
        self.variable_id = variable_entry_key
        self._data = variable_dict
        self.table = table
        self.frequency = self._data["frequency"]
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
        with open(path) as f:
            self._data = json.load(f)
        self._header_sanity_checks()
        self._assign_variable_entries()

        match = re.match(r"Table (?P<table_id>\w+)$", self._data["Header"]["table_id"])
        if not match:
            raise ValueError(f"Cannot determine table_id: <{path}>")
        self.table_id = match.group("table_id")

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
        for variable_dict in self._data["variable_entry"]:
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
        return self._data["approx_interval"]
