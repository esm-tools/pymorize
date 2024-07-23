"""
Yet another calendar implementation...

This module provides functions for listing files for a specific date range
"""

import time

import pendulum
from loguru import logger


def year_bounds_major_digits(first, last, step, binning_digit):
    """
    Generate year ranges with a specific first digit.

    This function generates a list of year ranges (bounds) where each range starts with a specific digit (binning_digit).
    The ranges are generated from a given start year (first) to an end year (last) with a specific step size.

    Parameters
    ----------
    first : int
        The first year in the range.
    last : int
        The last year in the range.
    step : int
        The step size for the range.
    binning_digit : int
        The digit that each range should start with.

    Returns
    -------
    list
        A list of lists where each inner list is a range of years.

    Raises
    ------
    ValueError
        If the binning_digit is greater than 10.

    Examples
    --------
    >>> year_bounds_major_digits(2000, 2010, 2, 2)
    [[2000, 2001], [2002, 2003], [2004, 2005], [2006, 2007], [2008, 2009], [2010, 2010]]

    >>> year_bounds_major_digits(2000, 2010, 3, 3)
    [[2000, 2002], [2003, 2005], [2006, 2008], [2009, 2010]]

    Notes
    -----
    This function uses a while loop to iterate through the years from first to last.
    It checks the ones digit of the current year and compares it with the binning_digit to determine the start of a new range.
    If the first range is undersized (i.e., the binning_digit is in the ones digit of the first few years),
    the function will continue to increment the current year until it hits the binning_digit.
    If the first range is not undersized, the function will continue to increment the current year until it hits the next binning_digit.
    Once a range is completed, it is appended to the bounds list and the process continues until the last year is reached.
    """
    # NOTE(PG): This is a bit hacky and difficult to read, but all the tests pass...
    if binning_digit >= 10:
        raise ValueError("Give a binning_digit less than 10")
    bounds = []
    current_location = bin_start = first
    first_bin_is_undersized = binning_digit in [
        i % 10 for i in range(first, first + step)
    ]
    bin_end = "underfull bin" if first_bin_is_undersized else bin_start + step
    first_bin_empty = True

    while current_location <= last:
        ones_digit = current_location % 10

        if first_bin_empty:
            if first_bin_is_undersized:
                # Go until you hit the binning digit
                if ones_digit != binning_digit:
                    current_location += 1
                    ones_digit = current_location % 10
                else:
                    bounds.append([bin_start, current_location - 1])
                    first_bin_empty = False
                    bin_start = current_location
            else:
                # Go until you hit the next binning digit
                if ones_digit == binning_digit:
                    bounds.append([bin_start, current_location - 1])
                    first_bin_empty = False
                    bin_start = current_location
                else:
                    current_location += 1
        else:
            bin_end = bin_start + step
            current_location += 1
            if current_location == bin_end or current_location > last:
                bounds.append([bin_start, min(current_location - 1, last)])
                bin_start = current_location
    return bounds


class CalendarRange:

    def __init__(
        self,
        start: pendulum.datetime,
        end: pendulum.datetime,
        freq: pendulum.Duration = pendulum.duration(months=1),
        periods: int = None,
    ):
        # Determine which 3 are given
        # If freq is given, calculate periods
        if freq:
            if periods:
                raise ValueError("Cannot specify both freq and periods")
            periods = (end - start) // freq
        # If periods is given, calculate freq
        elif periods:
            freq = (end - start) // periods
        # If none are given, raise an error
        else:
            raise ValueError("must specify either freq or periods")
        # Create range
        self._range = [start + i * freq for i in range(periods)]
        self._start = start
        self._end = end
        self._periods = periods

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    def __contains__(self, date_to_check):
        return date_to_check in self._range

    def __len__(self):
        return len(self._range)

    def __iter__(self):
        return iter(self._range)

    def __getitem__(self, index):
        return self._range[index]

    def __repr__(self):
        return f"CalendarRange(start={self._start}, end={self._end}, periods={self._periods})"

    def __str__(self):
        return f"{self._start} to {self._end} in {self._periods} periods"

    def __list__(self) -> list:
        return self._range

    @classmethod
    def from_bounds(cls, bounds, freq=pendulum.duration(months=1), periods=None):
        clses = []
        for start, end in bounds:
            clses.append(cls(start, end, freq, periods))
        return *clses
