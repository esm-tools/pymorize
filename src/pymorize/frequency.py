from enum import Enum


class TimeMethods(Enum):
    """Various time methods declared in CMIP"""

    MEAN = "MEAN"
    INSTANTANEOUS = "INSTANTANEOUS"
    CLIMATOLOGY = "CLIMATOLOGY"
    NONE = "NONE"


CMIP_FREQUENCIES = {
    "3hr": 3.0 / 24,
    "6hrLev": 6.0 / 24,
    "6hrPlev": 6.0 / 24,
    "6hrPlevPt": 6.0 / 24,
    "AERday": 1.0,
    ############################################################################################
    # NOTE: for AERhr, data request 01.00.27 says "1.0" here, but this seems to be wrong
    # NOTE: Taken from Jan Hegewald's seamore tool.
    "AERhr": 1.0 / 24,
    ############################################################################################
    "AERmon": 30.0,
    "AERmonZ": 30.0,
    "Amon": 30.0,
    "CF3hr": 3.0 / 24,
    "CFday": 1.0,
    "CFmon": 30.0,
    "day": 1.0,
    "E3hr": 3.0 / 24,
    "E3hrPt": 3.0 / 24,
    "E6hrZ": 6.0 / 24,
    "Eday": 1.0,
    "EdayZ": 1.0,
    "Emon": 30.0,
    "EmonZ": 30.0,
    "Eyr": 365.0,
    "ImonAnt": 30.0,
    "ImonGre": 30.0,
    "IyrAnt": 365.0,
    "IyrGre": 365.0,
    "LImon": 30.0,
    "Lmon": 30.0,
    "Oclim": 30.0,
    "Oday": 1.0,
    "Odec": 3650.0,
    "Omon": 30.0,
    "Oyr": 365.0,
    "SIday": 1.0,
    "SImon": 30.0,
}
"""dict : A dictionary mapping CMIP6 frequency names to the number of days in that frequency."""


class Frequency:
    def __init__(self, name, approx_interval, time_method=TimeMethods.MEAN):
        self.name = name
        self.approx_interval = approx_interval
        self.time_method = time_method

    def __eq__(self, other):
        if isinstance(other, Frequency):
            return self.name == other.name
        return False

    def __lt__(self, other):
        return self.approx_interval < other.approx_interval

    @classmethod
    def for_name(cls, n):
        freq = next((f for f in ALL if f.name == n), None)
        if not freq:
            raise ValueError(f"Cannot determine Frequency object for {n}")
        return freq


# Defining the ALL list with Frequency instances
ALL = [
    Frequency("1hr", 1.0 / 24),
    Frequency("3hr", 3.0 / 24),
    Frequency("6hr", 6.0 / 24),
    Frequency("day", 1.0),  # there is no dayPt frequency
    Frequency("mon", 30.0),
    Frequency("yr", 365.0),
    Frequency("dec", 3650.0),
    Frequency("1hrPt", 1.0 / 24, TimeMethods.INSTANTANEOUS),
    Frequency("3hrPt", 3.0 / 24, TimeMethods.INSTANTANEOUS),
    Frequency("6hrPt", 6.0 / 24, TimeMethods.INSTANTANEOUS),
    Frequency("monPt", 30.0, TimeMethods.INSTANTANEOUS),
    Frequency("yrPt", 365.0, TimeMethods.INSTANTANEOUS),
    Frequency("1hrCM", 1.0 / 24, TimeMethods.CLIMATOLOGY),
    Frequency("fx", 0, TimeMethods.NONE),
    Frequency("monC", 30.0, TimeMethods.CLIMATOLOGY),
    Frequency(
        "subhrPt", 0.017361, TimeMethods.INSTANTANEOUS
    ),  # there is no subhr time:mean
]

# Adding a global reference to ALL frequencies
Frequency.ALL = ALL
