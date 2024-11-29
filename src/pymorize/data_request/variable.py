"""
This module defines the ``DataRequestVariable`` abstract base class and its concrete implementation ``CMIP6DataRequestVariable``.

The ``DataRequestVariable`` class outlines the necessary properties and methods that any variable class should implement.
It includes properties such as frequency, modeling realm, standard name, units, cell methods, cell measures,
long name, comment, dimensions, out name, type, positive direction, valid minimum and maximum values,
acceptable minimum and maximum mean absolute values, and the table name.

The ``CMIP6DataRequestVariable`` class is a concrete implementation of the ``DataRequestVariable`` class, specifically for CMIP6 variables.
It uses the ``dataclass`` decorator to automatically generate the ``__init__``, ``__repr__``, and other special methods.

The module also provides class methods for constructing ``DataRequestVariable`` instances from dictionaries and JSON files,
as well as a method for converting a ``DataRequestVariable`` instance to a dictionary representation.
"""

import json
import pathlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


class DataRequestVariable(ABC):
    """Abstract base class for a generic variable."""

    _type_strings = {
        "real": float,
    }
    """dict: conversion of string names in the tables to actual Python types"""

    #################################################################
    # Properties a DataRequestVariable needs to have
    #################################################################

    @property
    @abstractmethod
    def frequency(self) -> str:  # Or should this return Frequency?
        """Frequency of this variable"""

    @property
    @abstractmethod
    def modeling_realm(self) -> str:
        """Modeling Realm of this variable"""

    @property
    @abstractmethod
    def standard_name(self) -> str:
        """The CF standard name of the variable"""

    @property
    @abstractmethod
    def units(self) -> str:
        """The units of the variable"""

    @property
    @abstractmethod
    def cell_methods(self) -> str:
        """Methods applied to the cell"""
        # FIXME(PG): I have no idea what this is

    @property
    @abstractmethod
    def cell_measures(self) -> str:
        """What this cell measure"""
        # FIXME(PG): I have no idea what this is

    @property
    @abstractmethod
    def long_name(self) -> str:
        """The CF long name for this variable"""

    @property
    @abstractmethod
    def comment(self) -> str:
        """Comment for NetCDF attributes"""

    @property
    @abstractmethod
    def dimensions(self) -> tuple[str, ...]:
        """Dimensions of this variable"""

    @property
    @abstractmethod
    def out_name(self) -> str:
        """Short name (array name) of this variable"""

    @property
    @abstractmethod
    def typ(self) -> type:
        """The type of this array: int, float, str"""

    @property
    @abstractmethod
    def positive(self) -> str:
        """For 3-D variables, which direction is up/down"""

    @property
    @abstractmethod
    def valid_min(self) -> float:
        """Valid minimum"""

    @property
    @abstractmethod
    def valid_max(self) -> float:
        """Valid maximum"""

    @property
    @abstractmethod
    def ok_min_mean_abs(self) -> float:
        """ok minimum, mean, and absolute value"""

    @property
    @abstractmethod
    def ok_max_mean_abs(self) -> float:
        """ok maximum, mean, and absolute value"""

    @property
    @abstractmethod
    def table_name(self) -> Optional[str]:
        """The table this variable is define in"""

    @property
    @abstractmethod
    def attrs(self) -> dict:
        """Attributes to update the Xarray DataArray with"""

    #################################################################
    # Class methods for construction
    #################################################################
    @classmethod
    def from_dict(cls, data: dict) -> "DataRequestVariable":
        """Create a DataRequestVariable instance from a dictionary."""
        typ = cls._type_strings.get(data["type"])
        if typ is None:
            raise ValueError(f"Unsupported type: {data['type']}")
        return cls(
            frequency=data["frequency"],
            modeling_realm=data["modeling_realm"],
            standard_name=data["standard_name"],
            units=data["units"],
            cell_methods=data["cell_methods"],
            cell_measures=data["cell_measures"],
            long_name=data["long_name"],
            comment=data["comment"],
            dimensions=tuple(
                data["dimensions"].split(" ")
            ),  # NOTE(PG): tuple, because of immutability
            out_name=data["out_name"],
            typ=cls._type_strings[data["type"]],
            positive=data["positive"],
            valid_min=data["valid_min"],
            valid_max=data["valid_max"],
            ok_min_mean_abs=data["ok_min_mean_abs"],
            ok_max_mean_abs=data["ok_max_mean_abs"],
            table_name=data.get("table_name"),
        )

    @classmethod
    def from_json_table_file(cls, filename: str, varname: str) -> "DataRequestVariable":
        with open(filename, "r") as f:
            data = json.load(f)["variable_entry"][varname]
            data["table_name"] = pathlib.Path(filename).stem
            return cls.from_dict(data)

    #################################################################
    # Methods for serialization
    #################################################################
    def to_dict(self) -> dict:
        """Convert the variable to a dictionary representation"""
        return self.__dict__

    #################################################################
    # Other methods
    #################################################################
    @abstractmethod
    def global_attrs(self, override_dict: dict = None) -> dict:
        """Global attributes for this variable, used to set on the xr.Dataset"""


@dataclass
class CMIP6DataRequestVariable(DataRequestVariable):
    frequency: str
    modeling_realm: str
    standard_name: str
    units: str
    cell_methods: str
    cell_measures: str
    long_name: str
    comment: str
    dimensions: tuple[str, ...]
    out_name: str
    typ: type
    positive: str
    valid_min: float
    valid_max: float
    ok_min_mean_abs: float
    ok_max_mean_abs: float
    table_name: Optional[str] = None

    @classmethod
    def from_json_table_file(
        cls, filename: str, varname: str
    ) -> "CMIP6DataRequestVariable":
        with open(filename, "r") as f:
            data = json.load(f)["variable_entry"][varname]
            data["table_name"] = pathlib.Path(filename).stem.replace("CMIP6_", "")
            return cls.from_dict(data)

    @property
    def attrs(self) -> dict:
        return {
            "standard_name": self.standard_name,
            "long_name": self.long_name,
            "units": self.units,
            "cell_methods": self.cell_methods,
            "cell_measures": self.cell_measures,
        }

    def global_attrs(self, override_dict: dict = None) -> dict:
        """Return a dictionary of global attributes for a CMIP6 variable

        Parameters
        ----------
        override_dict : dict
            A dictionary of attributes to override the default values
        """
        override_dict = override_dict or {}
        # FIXME: This needs to come from the CVs somehow
        rdict = {
            "Conventions": None,
            "activity_id": None,
            "creation_date": None,
            "data_specs_version": None,
            "experiment": None,
            "experiment_id": None,
            "forcing_index": None,
            "frequency": None,
            "further_info_url": None,
            "grid": None,
            "grid_label": None,
            "initialization_index": None,
            "institution": None,
            "institution_id": None,
            "license": None,
            "mip_era": None,
            "nominal_resolution": None,
            "physics_index": None,
            "product": None,
            "realization_index": None,
            "realm": None,
            "source": None,
            "source_id": None,
            "source_type": None,
            "sub_experiment": None,
            "sub_experiment_id": None,
            "table_id": None,
            "tracking_id": None,
            "variable_id": None,
            "variant_label": None,
        }
        rdict.update(override_dict)
        return rdict
