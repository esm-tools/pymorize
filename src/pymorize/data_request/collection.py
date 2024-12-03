from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict

import deprecation

from .factory import MetaFactory
from .table import DataRequestTable


class DataRequest(ABC, metaclass=MetaFactory):

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
    @deprecation.deprecated(details="Use from_directory instead.")
    @abstractmethod
    def from_tables_dir(cls, directory: str) -> "DataRequest":
        """Create a DataRequest from a directory of tables."""
        raise NotImplementedError


class IgnoreTableFiles(Enum):
    """Table files to ignore when reading from a directory."""

    CV_TEST = "CMIP6_CV_test.json"
    COORDINATE = "CMIP6_coordinate.json"
    CV = "CMIP6_CV.json"
    FORMULA_TERMS = "CMIP6_formula_terms.json"
    GRIDS = "CMIP6_grids.json"
    INPUT_EXAMPLE = "CMIP6_input_example.json"
