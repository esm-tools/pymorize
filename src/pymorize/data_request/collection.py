from abc import ABC, abstractmethod
from enum import Enum


class DataRequest(ABC):

    @abstractmethod
    @classmethod
    def from_tables(cls, tables: Dict[str, "DataRequestTable"]) -> "DataRequest":
        """Create a DataRequest from a dictionary of tables."""
        raise NotImplementedError

    @abstractmethod
    @classmethod
    def from_directory(cls, directory: str) -> "DataRequest":
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
