import numpy as np
import pytest
import xarray as xr


# @pytest.mark.parametrize("test_input", a_list)
def test_sort_dimensions(dummy_array, rule_with_unsorted_data):
    """Test to check that dimensions are sorted correctly"""
    from pymorize.generic import sort_dimensions

    dummy_array = sort_dimensions(dummy_array, rule_with_unsorted_data)

    assert dummy_array.dims == tuple(rule_with_unsorted_data.array_order)
