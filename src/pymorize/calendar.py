"""
Yet another calendar implementation...

This module provides functions for listing files for a specific date range
"""

import pendulum


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
