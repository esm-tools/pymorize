# Sample Test passing with nose and pytest
import os

import pytest

from pymorize.generic import CMORizer


@pytest.fixture
def fesom_sample():
    return os.path.join(os.path.dirname(__file__), "fesom_sample.yaml")


def test_create_cmorizer_from_yaml(fesom_sample):
    with open(fesom_sample, "r") as f:
        cmor_engine = CMORizer.from_yaml(f)
