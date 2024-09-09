import pytest

from pymorize.data_request import DataRequestVariable
from pymorize.rule import Rule


@pytest.fixture
def simple_rule():
    return Rule(
        input_patterns=[
            r"/some/files/containing/var1.*.nc",
            r"/some/other/files/containing/var1_(?P<year>\d{4}).nc",
        ],
        cmor_variable="var1",
        pipelines=["pymorize.pipeline.TestingPipeline"],
    )


@pytest.fixture
def rule_with_mass_units():
    r = Rule(
        input_patterns=[
            r"/some/files/containing/var1.*.nc",
            r"/some/other/files/containing/var1_(?P<year>\d{4}).nc",
        ],
        cmor_variable="var1",
        pipelines=["pymorize.pipeline.TestingPipeline"],
        data_request_variables=[
            DataRequestVariable(
                variable_id="var1",
                unit="kg",
                description="Some description",
                time_method="instant",
                table="Some Table",
                frequency="mon",
                realms=["atmos"],
                standard_name="some_standard_name",
                cell_methods="time: mean",
                cell_measures="area: areacella",
            )
        ],
    )
    r.data_request_variable = r.data_request_variables[0]
    return r


@pytest.fixture
def rule_with_units():
    r = Rule(
        input_patterns=[
            r"/some/files/containing/var1.*.nc",
            r"/some/other/files/containing/var1_(?P<year>\d{4}).nc",
        ],
        cmor_variable="var1",
        pipelines=["pymorize.pipeline.TestingPipeline"],
        data_request_variables=[
            DataRequestVariable(
                variable_id="var1",
                unit="kg m-2 s-1",
                description="Some description",
                time_method="instant",
                table="Some Table",
                frequency="mon",
                realms=["atmos"],
                standard_name="some_standard_name",
                cell_methods="time: mean",
                cell_measures="area: areacella",
            )
        ],
    )
    r.data_request_variable = r.data_request_variables[0]
    return r
