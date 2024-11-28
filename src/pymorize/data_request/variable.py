import json
import pathlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


class Variable(ABC):
    """Abstract base class for a generic variable."""

    _type_strings = {
        "real": float,
    }
    """dict: conversion of string names in the tables to actual Python types"""

    #################################################################
    # Properties a Variable needs to have
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

    #################################################################
    # Class methods for construction
    #################################################################
    @classmethod
    def from_dict(cls, data: dict) -> "Variable":
        """Create a Variable instance from a dictionary."""
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
    def from_json_table_file(cls, filename: str, varname: str) -> "Variable":
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
    # Nothing yet....


@dataclass
class CMIP6Variable(Variable):
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
