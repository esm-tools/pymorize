import pendulum

import pymorize.calendar
from pymorize.calendar import CalendarRange


def setup_calendar_range():
    start = pendulum.datetime(2022, 1, 1)
    end = pendulum.datetime(2022, 12, 31)
    freq = pendulum.duration(months=1)
    return CalendarRange(start, end, freq)


def test_init():
    calendar_range = setup_calendar_range()
    assert calendar_range.start == pendulum.datetime(2022, 1, 1)
    assert calendar_range.end == pendulum.datetime(2022, 12, 31)
    assert len(calendar_range) == 12


def test_contains():
    calendar_range = setup_calendar_range()
    assert pendulum.datetime(2022, 5, 1) in calendar_range
    assert pendulum.datetime(2023, 1, 1) not in calendar_range


def test_len():
    calendar_range = setup_calendar_range()
    assert len(calendar_range) == 12


def test_iter():
    calendar_range = setup_calendar_range()
    dates = [date for date in calendar_range]
    assert len(dates) == 12


def test_getitem():
    calendar_range = setup_calendar_range()
    assert calendar_range[0] == pendulum.datetime(2022, 1, 1)
    assert calendar_range[-1] == pendulum.datetime(2022, 12, 31)


def test_repr():
    calendar_range = setup_calendar_range()
    assert (
        repr(calendar_range)
        == "CalendarRange(start=2022-01-01T00:00:00+00:00, end=2022-12-31T00:00:00+00:00, periods=12)"
    )


def test_str():
    calendar_range = setup_calendar_range()
    assert (
        str(calendar_range)
        == "2022-01-01T00:00:00+00:00 to 2022-12-31T00:00:00+00:00 in 12 periods"
    )


def test_from_bounds():
    bounds = [(pendulum.datetime(2022, 1, 1), pendulum.datetime(2022, 12, 31))]
    freq = pendulum.duration(months=1)
    calendar_ranges = CalendarRange.from_bounds(bounds, freq)
    assert len(calendar_ranges) == 1
    assert calendar_ranges[0].start == pendulum.datetime(2022, 1, 1)
    assert calendar_ranges[0].end == pendulum.datetime(2022, 12, 31)


def test_from_bounds_multiple():
    bounds = [
        (pendulum.datetime(2022, 1, 1), pendulum.datetime(2022, 6, 30)),
        (pendulum.datetime(2022, 7, 1), pendulum.datetime(2022, 12, 31)),
    ]
    freq = pendulum.duration(months=1)
    calendar_ranges = CalendarRange.from_bounds(bounds, freq)
    assert len(calendar_ranges) == 2
    assert calendar_ranges[0].start == pendulum.datetime(2022, 1, 1)
    assert calendar_ranges[0].end == pendulum.datetime(2022, 6, 30)
    assert calendar_ranges[1].start == pendulum.datetime(2022, 7, 1)
    assert calendar_ranges[1].end == pendulum.datetime(2022, 12, 31)


def test_from_bounds_integers():
    bounds = [(2700, 2720)]
    calendar_ranges = CalendarRange.from_bounds(bounds)
    assert len(calendar_ranges) == 1
    assert calendar_ranges[0].start == pendulum.datetime(2700, 1, 1)
    assert calendar_ranges[0].end == pendulum.datetime(2720, 12, 31)


def test_year_bounds_major_digits_first_can_end_with_binning_digit():
    bounds = pymorize.calendar.year_bounds_major_digits(
        first=2700, last=2720, step=10, binning_digit=1
    )
    assert [[2700, 2700], [2701, 2710], [2711, 2720]] == bounds


def test_year_bounds_major_digits_can_start_1before_major_digit1():
    bounds = pymorize.calendar.year_bounds_major_digits(
        first=2050, last=2070, step=10, binning_digit=1
    )
    assert [[2050, 2050], [2051, 2060], [2061, 2070]] == bounds


def test_year_bounds_major_digits_can_have_no_complete_range():
    bounds = pymorize.calendar.year_bounds_major_digits(
        first=2050, last=2055, step=10, binning_digit=1
    )
    assert [[2050, 2050], [2051, 2055]] == bounds


def test_year_bounds_major_digits_can_start_3before_major_digit3():
    bounds = pymorize.calendar.year_bounds_major_digits(
        first=2050, last=2070, step=10, binning_digit=3
    )
    assert [[2050, 2052], [2053, 2062], [2063, 2070]] == bounds


def test_year_bounds_major_digits_can_start_9before_major_digit1():
    bounds = pymorize.calendar.year_bounds_major_digits(
        first=2042, last=2070, step=10, binning_digit=1
    )
    assert [[2042, 2050], [2051, 2060], [2061, 2070]] == bounds


def test_year_bounds_major_digits_can_start_1before_major_digit1_with_step20():
    bounds = pymorize.calendar.year_bounds_major_digits(
        first=2050, last=2080, step=20, binning_digit=1
    )
    assert [[2050, 2050], [2051, 2070], [2071, 2080]] == bounds


def test_year_bounds_major_digits_can_start_3before_major_digit3_with_step5():
    bounds = pymorize.calendar.year_bounds_major_digits(
        first=2050, last=2070, step=5, binning_digit=3
    )
    assert [
        [2050, 2052],
        [2053, 2057],
        [2058, 2062],
        [2063, 2067],
        [2068, 2070],
    ] == bounds


def test_year_bounds_major_digits_can_start_1before_major_digit1_with_step1():
    bounds = pymorize.calendar.year_bounds_major_digits(
        first=2050, last=2055, step=1, binning_digit=1
    )
    assert [
        [2050, 2050],
        [2051, 2051],
        [2052, 2052],
        [2053, 2053],
        [2054, 2054],
        [2055, 2055],
    ] == bounds
