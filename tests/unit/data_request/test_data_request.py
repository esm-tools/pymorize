from pymorize.data_request.collection import CMIP6DataRequest, CMIP7DataRequest


def test_cmip6_from_git():
    request = CMIP6DataRequest.from_git()
    # If the function worked, we should get tables:
    assert request.tables


def test_cmip7_from_vendored_json():
    request = CMIP7DataRequest.from_vendored_json()
    # If the function worked, we should get tables:
    assert request.tables
    # And we should get variables:
    assert request.variables
