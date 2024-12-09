from pymorize.data_request.collection import CMIP6DataRequest


def test_cmip6_from_git():
    request = CMIP6DataRequest.from_git()
    # If the function worked, we should get tables:
    assert request.tables
