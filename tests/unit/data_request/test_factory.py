import pytest

from pymor.core.factory import create_factory
from pymor.data_request.collection import CMIP6DataRequest, DataRequest
from pymor.data_request.table import CMIP6DataRequestTable, DataRequestTable
from pymor.data_request.variable import CMIP6DataRequestVariable, DataRequestVariable


@pytest.mark.parametrize(
    ("input_class", "output_class"),
    [
        (DataRequest, CMIP6DataRequest),
        (DataRequestVariable, CMIP6DataRequestVariable),
        (DataRequestTable, CMIP6DataRequestTable),
    ],
)
def test_factory(input_class, output_class):
    Factory = create_factory(input_class)
    Product = Factory.get("CMIP6")
    assert Product == output_class


def test_factory_raises():
    Factory = create_factory(DataRequest)
    with pytest.raises(ValueError):
        Factory.get("CMIP4")
