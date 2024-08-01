import re

import pytest

from pymorize.pipeline import TestingPipeline
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


def test_direct_init(simple_rule):
    rule = simple_rule
    assert all(isinstance(ip, re.Pattern) for ip in rule.input_patterns)
    assert isinstance(rule.cmor_variable, str)
    assert all(isinstance(p, str) for p in rule.pipelines)


def test_from_dict():
    data = {
        "input_patterns": [
            r"/some/files/containing/var1.*.nc",
            r"/some/other/files/containing/var1_(?P<year>\d{4}).nc",
        ],
        "cmor_variable": "var1",
        "pipelines": ["pymorize.pipeline.TestingPipeline"],
    }
    rule = Rule.from_dict(data)
    assert all(isinstance(ip, re.Pattern) for ip in rule.input_patterns)
    assert isinstance(rule.cmor_variable, str)
    assert all(isinstance(p, str) for p in rule.pipelines)


def test_from_yaml():
    yaml_str = """
    input_patterns: 
      - /some/files/containing/var1.*.nc
      - /some/other/files/containing/var1_(?P<year>\d{4}).nc
    cmor_variable: var1
    pipelines: 
      - pymorize.pipeline.TestingPipeline
    """
    rule = Rule.from_yaml(yaml_str)
    assert all(isinstance(ip, re.Pattern) for ip in rule.input_patterns)
    assert isinstance(rule.cmor_variable, str)
    assert all(isinstance(p, str) for p in rule.pipelines)


def test_match_pipelines(simple_rule):
    rule = simple_rule
    pipelines = [TestingPipeline(name="pymorize.pipeline.TestingPipeline")]
    rule.match_pipelines(pipelines)
