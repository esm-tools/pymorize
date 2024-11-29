import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

import pendulum
from semver.version import Version

from .variable import DataRequestVariable


class DataRequestTable(ABC):
    """Abstract base class for a generic data request table."""

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Name of the table."""
        pass

    @property
    @abstractmethod
    def variables(self) -> List[DataRequestVariable]:
        """List of variables in the table."""
        pass

    @abstractmethod
    def get_variable(self, name: str) -> DataRequestVariable:
        """Retrieve a variable's details by name."""
        pass

    @property
    @abstractmethod
    def header(self) -> "DataRequestTableHeader":
        """Header of the table."""
        pass


class DataRequestTableHeader(ABC):

    @property
    @abstractmethod
    def data_specs_version(self) -> Version:
        """Data specifications version."""
        pass

    @property
    @abstractmethod
    def cmor_version(self) -> Version:
        """CMOR version."""
        pass

    @property
    @abstractmethod
    def table_id(self) -> str:
        """Name of the table."""
        pass

    @property
    @abstractmethod
    def realm(self) -> str:
        """Realm of the table."""
        pass

    @property
    @abstractmethod
    def table_date(self) -> pendulum.date:
        """Date of the table."""
        pass

    @property
    @abstractmethod
    def missing_value(self) -> float:
        """Missing Value"""

    @property
    @abstractmethod
    def int_missing_value(self) -> int:
        """Integer missing value"""

    @property
    @abstractmethod
    def product(self) -> str:
        """Product"""

    @property
    @abstractmethod
    def approx_interval(self) -> float:
        """Approximate interval (time in days)"""

    @property
    @abstractmethod
    def generic_levels(self) -> List[str]:
        """Generic levels"""
        pass

    @property
    @abstractmethod
    def mip_era(self) -> str:
        """MIP era"""
        pass

    @property
    @abstractmethod
    def Conventions(self) -> str:
        """Conventions"""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "DataRequestTableHeader":
        """Create a DataRequestTableHeader from a dictionary."""
        pass


@dataclass
class CMIP6DataRequestTableHeader(DataRequestTableHeader):
    # NOTE(PG): The defaults here refer to the CMIP6 Data Request Tables
    # found in commit 1131220 of the cmip6-cmor-tables repository. Some
    # of these defaults might not be correct for later versions.
    #
    # Manual cleanup in the hard-coded defaults:
    # - data_specs_version: "01.00.33" -> "1.0.33" to match semver
    _table_id: str
    _realm: str
    _table_date: pendulum.Date
    _approx_interval: float
    _generic_levels: List[str]

    # Properties with known defaults:
    _HARD_CODED_DATA_SPECS_OLD = "01.00.33"
    _HARD_CODED_DATA_SPECS_NEW = "1.0.33"
    _data_specs_version: Version = Version.parse(
        _HARD_CODED_DATA_SPECS_NEW,
        optional_minor_and_patch=True,
    )
    _cmor_version: Version = Version.parse(
        "3.5",
        optional_minor_and_patch=True,
    )
    _mip_era: str = "CMIP6"
    _Conventions: str = "CF-1.7 CMIP-6.2"
    _missing_value: float = 1.0e20
    _int_missing_value: int = -999
    _product: str = "model-output"

    @classmethod
    def from_dict(cls, data: dict) -> "CMIP6DataRequestTableHeader":
        # The input dict needs to have these, since we have no defaults:
        extracted_data = dict(
            _table_id=data["table_id"].lstrip("Table "),
            _realm=data["realm"],
            _table_date=pendulum.parse(data["table_date"], strict=False).date(),
            _approx_interval=float(data["approx_interval"]),
            _generic_levels=data["generic_levels"].split(" "),
        )
        # Optionally get the rest, which might not be present:
        for key in cls.__dataclass_fields__.keys():
            if key.lstrip("_") in data and key not in extracted_data:
                extracted_data[key] = data[key.lstrip("_")]
        # Handle Version conversions
        if "_data_specs_version" in extracted_data:
            extracted_data["_data_specs_version"] = Version.parse(
                extracted_data["_data_specs_version"].replace(
                    cls._HARD_CODED_DATA_SPECS_OLD,
                    cls._HARD_CODED_DATA_SPECS_NEW,
                ),
                optional_minor_and_patch=True,
            )
        if "_cmor_version" in extracted_data:
            extracted_data["_cmor_version"] = Version.parse(
                extracted_data["_cmor_version"],
                optional_minor_and_patch=True,
            )
        # Handle types for missing_value and int_missing_value
        if "_missing_value" in extracted_data:
            extracted_data["_missing_value"] = float(extracted_data["_missing_value"])
        if "_int_missing_value" in extracted_data:
            extracted_data["_int_missing_value"] = int(
                extracted_data["_int_missing_value"]
            )
        return cls(**extracted_data)

    @property
    def table_id(self) -> str:
        return self._table_id

    @property
    def realm(self) -> str:
        return self._realm

    @property
    def table_date(self) -> pendulum.Date:
        return self._table_date

    @property
    def missing_value(self) -> float:
        return self._missing_value

    @property
    def int_missing_value(self) -> int:
        return self._int_missing_value

    @property
    def product(self) -> str:
        return self._product

    @property
    def approx_interval(self) -> float:
        return self._approx_interval

    @property
    def generic_levels(self) -> List[str]:
        return self._generic_levels

    @property
    def mip_era(self) -> str:
        return self._mip_era

    @property
    def Conventions(self) -> str:
        return self._Conventions

    @property
    def data_specs_version(self) -> Version:
        return self._data_specs_version

    @property
    def cmor_version(self) -> Version:
        return self._cmor_version


@dataclass
class CMIP6JSONDataRequestTableHeader(CMIP6DataRequestTableHeader):

    @classmethod
    def from_json_file(cls, jfile) -> "CMIP6JSONDataRequestTableHeader":
        with open(jfile, "r") as f:
            data = json.load(f)
            header = data["Header"]
            return cls.from_dict(header)


class CMIP6DataRequestTable(DataRequestTable):
    """Concrete implementation of DataRequestTable for CMIP6."""

    def __init__(self, data: Dict[str, dict]):
        self._data = data

    @property
    def variables(self) -> List[str]:
        return list(self._data.keys())

    def get_variable(self, name: str) -> dict:
        return self._data.get(name, {})
