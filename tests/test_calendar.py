import xarray as xr

import pymorize.calendar


def test_simple_ranges_from_bounds():
    bounds = [(1, 5), (10, 15)]
    result = list(pymorize.calendar.simple_ranges_from_bounds(bounds))
    expected = [range(1, 6), range(10, 16)]
    assert result == expected


def test_single_range():
    bounds = [(1, 5)]
    result = pymorize.calendar.simple_ranges_from_bounds(bounds)
    expected = range(1, 6)
    assert result == expected


def test_single_range_single_element():
    bounds = [(3, 3)]
    result = pymorize.calendar.simple_ranges_from_bounds(bounds)
    expected = range(3, 4)
    assert result == expected


def test_single_range_negative():
    bounds = [(-5, -1)]
    result = pymorize.calendar.simple_ranges_from_bounds(bounds)
    expected = range(-5, 0)
    assert result == expected


def test_date_ranges_from_bounds():
    bounds = [("2020-01-01", "2020-01-31"), ("2020-02-01", "2020-02-29")]
    result = pymorize.calendar.date_ranges_from_bounds(bounds)
    expected = (
        xr.date_range(start="2020-01-01", end="2020-01-31", freq="M"),
        xr.date_range(start="2020-02-01", end="2020-02-29", freq="M"),
    )
    assert result == expected


def test_date_ranges_from_bounds_single_range():
    bounds = [("2020-01-01", "2020-12-31")]
    result = pymorize.calendar.date_ranges_from_bounds(bounds)
    expected = xr.date_range(start="2020-01-01", end="2020-12-31", freq="M")
    assert (result == expected).all()


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
