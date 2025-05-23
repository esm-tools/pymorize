import re

from pymor.core.pipeline import TestingPipeline
from pymor.core.rule import Rule


def test_direct_init(simple_rule):
    rule = simple_rule
    assert all(isinstance(ip, re.Pattern) for ip in rule.input_patterns)
    assert isinstance(rule.cmor_variable, str)
    assert all(isinstance(p, str) for p in rule.pipelines)


def test_from_dict():
    data = {
        "inputs": [
            {
                "path": "/some/files/containing/",
                "pattern": "var1.*.nc",
            },
            {
                "path": "/some/other/files/containing/",
                "pattern": r"var1_(?P<year>\d{4}).nc",
            },
        ],
        "cmor_variable": "var1",
        "pipelines": ["pymor.pipeline.TestingPipeline"],
    }
    rule = Rule.from_dict(data)
    assert all(isinstance(ip, re.Pattern) for ip in rule.input_patterns)
    assert isinstance(rule.cmor_variable, str)
    assert all(isinstance(p, str) for p in rule.pipelines)


def test_from_yaml():
    yaml_str = """
    inputs:
        - path: /some/files/containing/
          pattern: var1.*.nc
        - path: /some/other/files/containing/
          pattern: var1_(?P<year>\d{4}).nc
    cmor_variable: var1
    pipelines:
      - pymor.pipeline.TestingPipeline
    """  # noqa: W605
    rule = Rule.from_yaml(yaml_str)
    assert all(isinstance(ip, re.Pattern) for ip in rule.input_patterns)
    assert isinstance(rule.cmor_variable, str)
    assert all(isinstance(p, str) for p in rule.pipelines)


def test_match_pipelines(simple_rule):
    rule = simple_rule
    pipelines = [TestingPipeline(name="pymor.pipeline.TestingPipeline")]
    rule.match_pipelines(pipelines)
