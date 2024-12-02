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


class IgnoreTableFiles(Enum): ...
