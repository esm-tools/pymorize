import pytest

from pymorize.data_request import DataRequestVariable
from pymorize.rule import Rule


@pytest.fixture
def pi_uxarray_temp_rule(pi_uxarray_data):
    return Rule.from_dict(
        {
            "name": "temp",
            "experiment_id": "piControl",
            "output_directory": "./output",
            "source_id": "FESOM",
            "variant_label": "r1i1p1f1",
            "inputs": [
                {
                    "path": pi_uxarray_data,
                    "pattern": "temp.fesom..*.nc",
                },
            ],
            "cmor_variable": "thetao",
            "model_variable": "temp",
        }
    )


@pytest.fixture
def simple_rule():
    return Rule(
        inputs=[
            {
                "path": "/some/files/containing/",
                "pattern": "var1.*.nc",
            },
            {
                "path": "/some/other/files/containing/",
                "pattern": r"var1_(?P<year>\d{4}).nc",
            },
        ],
        cmor_variable="var1",
        pipelines=["pymorize.pipeline.TestingPipeline"],
    )


@pytest.fixture
def rule_with_mass_units():
    r = Rule(
        inputs=[
            {
                "path": "/some/files/containing/",
                "pattern": "var1.*.nc",
            },
            {
                "path": "/some/other/files/containing/",
                "pattern": r"var1_(?P<year>\d{4}).nc",
            },
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
        inputs=[
            {
                "path": "/some/files/containing/",
                "pattern": "var1.*.nc",
            },
            {
                "path": "/some/other/files/containing/",
                "pattern": r"var1_(?P<year>\d{4}).nc",
            },
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
