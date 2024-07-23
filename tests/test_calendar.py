import pymorize.calendar


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


def test_year_bounds_wrap_over():
    bounds = pymorize.calendar.year_bounds_major_digits(
        first=2058, last=2075, step=5, binning_digit=7
    )
    assert [[2058, 2062], [2063, 2066], [2067, 2072], [2073, 2075]] == bounds


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
