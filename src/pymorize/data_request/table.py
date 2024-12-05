import json
from abc import abstractmethod
from dataclasses import dataclass
from typing import List

import pendulum
from semver.version import Version

from .factory import MetaFactory
from .variable import CMIP6DataRequestVariable, DataRequestVariable

################################################################################
# BLUEPRINTS: Abstract classes for the data request tables
################################################################################


@dataclass
class DataRequestTable(metaclass=MetaFactory):
    """Abstract base class for a generic data request table."""

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Name of the table."""
        raise NotImplementedError

    @property
    @abstractmethod
    def variables(self) -> List[DataRequestVariable]:
        """List of variables in the table."""
        raise NotImplementedError

    @abstractmethod
    def get_variable(self, name: str) -> DataRequestVariable:
        """Retrieve a variable's details by name."""
        raise NotImplementedError

    @property
    @abstractmethod
    def header(self) -> "DataRequestTableHeader":
        """Header of the table."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "DataRequestTable":
        """Create a DataRequestTable from a dictionary."""
        raise NotImplementedError


################################################################################


@dataclass
class DataRequestTableHeader(metaclass=MetaFactory):
    @property
    @abstractmethod
    def data_specs_version(self) -> Version:
        """Data specifications version."""
        raise NotImplementedError

    @property
    @abstractmethod
    def cmor_version(self) -> Version:
        """CMOR version."""
        raise NotImplementedError

    @property
    @abstractmethod
    def table_id(self) -> str:
        """Name of the table."""
        raise NotImplementedError

    @property
    @abstractmethod
    def realm(self) -> str:
        """Realm of the table."""
        raise NotImplementedError

    @property
    @abstractmethod
    def table_date(self) -> pendulum.date:
        """Date of the table."""
        raise NotImplementedError

    @property
    @abstractmethod
    def missing_value(self) -> float:
        """Missing Value"""
        raise NotImplementedError

    @property
    @abstractmethod
    def int_missing_value(self) -> int:
        """Integer missing value"""
        raise NotImplementedError

    @property
    @abstractmethod
    def product(self) -> str:
        """Product"""
        raise NotImplementedError

    @property
    @abstractmethod
    def approx_interval(self) -> float:
        """Approximate interval (time in days)"""
        raise NotImplementedError

    @property
    @abstractmethod
    def generic_levels(self) -> List[str]:
        """Generic levels"""
        raise NotImplementedError

    @property
    @abstractmethod
    def mip_era(self) -> str:
        """MIP era"""
        raise NotImplementedError

    @property
    @abstractmethod
    def Conventions(self) -> str:
        """Conventions"""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "DataRequestTableHeader":
        """Create a DataRequestTableHeader from a dictionary."""
        raise NotImplementedError


################################################################################
# END BLUEPRINTS
################################################################################


@dataclass
class CMIP6DataRequestTableHeader(DataRequestTableHeader):
    ############################################################################
    # NOTE(PG): The defaults here refer to the CMIP6 Data Request Tables
    # found in commit 1131220 of the cmip6-cmor-tables repository. Some
    # of these defaults might not be correct for later versions.
    #
    # Manual cleanup in the hard-coded defaults:
    # - data_specs_version: "01.00.33" -> "1.0.33" to match semver
    ############################################################################

    # Properties without defaults:
    # ----------------------------
    _table_id: str
    _realm: str
    _table_date: pendulum.Date
    _approx_interval: float
    _generic_levels: List[str]

    # Properties with known defaults:
    # -------------------------------
    # NOTE(PG): I don't like doing it this way, but it is fastest to
    #           implement for right by now...
    # Key: Value --> Old: New
    _HARD_CODED_DATA_SPECS_REPLACEMENTS = {
        "01.00.33": "1.0.33",
        "01.00.27": "1.0.27",
    }
    _data_specs_version: Version = Version.parse(
        "1.0.33",
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
            for old_value, new_value in cls._HARD_CODED_DATA_SPECS_REPLACEMENTS.items():
                extracted_data["_data_specs_version"] = extracted_data[
                    "_data_specs_version"
                ].replace(old_value, new_value)
            extracted_data["_data_specs_version"] = Version.parse(
                extracted_data["_data_specs_version"],
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


################################################################################


@dataclass
class CMIP6JSONDataRequestTableHeader(CMIP6DataRequestTableHeader):
    @classmethod
    def from_json_file(cls, jfile) -> "CMIP6JSONDataRequestTableHeader":
        with open(jfile, "r") as f:
            data = json.load(f)
            header = data["Header"]
            return cls.from_dict(header)


################################################################################


class CMIP6DataRequestTable(DataRequestTable):
    """DataRequestTable for CMIP6."""

    # FIXME(PG): This might bite itself in the ass...
    def __init__(
        self,
        header: CMIP6DataRequestTableHeader,
        variables: List[DataRequestVariable],
    ):
        self._header = header
        self._variables = variables

    @property
    def variables(self) -> List[str]:
        return self._variables

    @property
    def header(self) -> CMIP6DataRequestTableHeader:
        return self._header

    @property
    def table_name(self) -> str:
        return self.header.table_id

    def get_variable(self, name: str, find_by="name") -> DataRequestVariable:
        """Returns the first variable with the matching name.

        Parameters
        ----------
        name : str

        Returns
        -------
        DataRequestVariable
        """
        for v in self._variables:
            if getattr(v, find_by) == name:
                return v
        raise ValueError(
            f"A Variable with the attribute {find_by}={name} not found in the table."
        )

    @classmethod
    def from_dict(cls, data: dict) -> "CMIP6DataRequestTable":
        header = CMIP6DataRequestTableHeader.from_dict(data["Header"])
        variables = [
            CMIP6DataRequestVariable.from_dict(v)
            for v in data["variable_entry"].values()
        ]
        return cls(header, variables)

    @classmethod
    def from_json_file(cls, jfile) -> "CMIP6DataRequestTable":
        with open(jfile, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


################################################################################
