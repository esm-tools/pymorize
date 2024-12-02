from pymorize.data_request.variable import CMIP6JSONDataRequestVariable


def test_init():
    variable = CMIP6JSONDataRequestVariable.from_json_file(
        "cmip6-cmor-tables/Tables/CMIP6_Omon.json",
        "thetao",
    )
    assert variable.name == "thetao"
