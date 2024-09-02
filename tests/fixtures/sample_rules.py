from pymorize.rule import Rule
import pytest


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
def rule_with_units():
    return Rule(
        input_patterns=[
            r"/some/files/containing/var1.*.nc",
            r"/some/other/files/containing/var1_(?P<year>\d{4}).nc",
        ],
        cmor_variable="var1",
        pipelines=["pymorize.pipeline.TestingPipeline"],
        cmor_units="kg m-2 s-1",
    )
