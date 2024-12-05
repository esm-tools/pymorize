import pathlib
from abc import abstractmethod
from enum import Enum
from typing import Dict

import deprecation

from .factory import MetaFactory
from .table import CMIP6DataRequestTable, DataRequestTable


class DataRequest(metaclass=MetaFactory):
    @classmethod
    @abstractmethod
    def from_tables(cls, tables: Dict[str, DataRequestTable]) -> "DataRequest":
        """Create a DataRequest from a dictionary of tables."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_directory(cls, directory: str) -> "DataRequest":
        """Create a DataRequest from a directory of tables."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_git(cls, url: str, branch: str = "master") -> "DataRequest":
        """Create a DataRequest from a git repository."""
        raise NotImplementedError

    @classmethod
    @deprecation.deprecated(details="Use from_directory instead.")
    @abstractmethod
    def from_tables_dir(cls, directory: str) -> "DataRequest":
        """Create a DataRequest from a directory of tables."""
        raise NotImplementedError


class CMIP6DataRequest(DataRequest):

    GIT_URL = "..."

    def __init__(
        self,
        tables: Dict[str, CMIP6DataRequestTable],
        flattable_variables: bool = True,
        include_table_headers_in_variables: bool = False,
    ):
        """
        Create a CMIP6DataRequest instance.

        Parameters
        ----------
        tables : Dict[str, DataRequestTable]
            A dictionary of tables.
        flattable_variables: bool, optional
            Whether or not to "flatten" tables by key, generating a unique key for each
            variable. This is composed of the table_id and variable_id. Default is True.
        include_table_headers_in_variables: bool, optional
            Whether or not to include the table header in the variable object. Default is False.
        """
        self.tables = tables
        self.variables = {}
        for table in tables.values():
            for variable in table.variables:
                if flattable_variables:
                    var_key = f"{table.table_id}.{variable.variable_id}"
                else:
                    var_key = variable.variable_id
                if include_table_headers_in_variables:
                    variable.table_header = table.header
                self.variables[var_key] = variable

    @classmethod
    def from_tables(cls, tables: Dict[str, DataRequestTable]) -> "CMIP6DataRequest":
        for table in tables.values():
            if not isinstance(table, DataRequestTable):
                raise ValueError("All tables must be instances of DataRequestTable.")
        return cls(tables)

    @classmethod
    def from_directory(cls, directory: str) -> "CMIP6DataRequest":
        tables = {}
        directory = pathlib.Path(directory)
        for file in directory.iterdir():
            if file.is_file() and file.suffix == ".json":
                table = CMIP6DataRequestTable.from_json_file(file)
                tables[table.table_id] = table

        for table in tables.values():
            if table in CMIP6IgnoreTableFiles:
                tables.pop(table)  # Remove the table from the dictionary

        return cls(tables)

    @classmethod
    def from_git(cls, url: str = None, branch: str = "master") -> "CMIP6DataRequest":
        if url is None:
            url = cls.GIT_URL
        raise NotImplementedError

    @classmethod
    @deprecation.deprecated(details="Use from_directory instead.")
    def from_tables_dir(cls, directory: str) -> "CMIP6DataRequest":
        return cls.from_directory(directory)

    @classmethod
    def from_variables(cls, variables: Dict[str, Dict[str, str]]) -> "CMIP6DataRequest":
        tables = {}
        instance = cls(tables)
        instance.variables = variables
        return instance


class CMIP6IgnoreTableFiles(Enum):
    """Table files to ignore when reading from a directory."""

    CV_TEST = "CMIP6_CV_test.json"
    COORDINATE = "CMIP6_coordinate.json"
    CV = "CMIP6_CV.json"
    FORMULA_TERMS = "CMIP6_formula_terms.json"
    GRIDS = "CMIP6_grids.json"
    INPUT_EXAMPLE = "CMIP6_input_example.json"
