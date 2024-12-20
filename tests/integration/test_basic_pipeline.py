"""
Integration test that mimics the CLI command for a minimal config
"""

import shutil

import pytest
import yaml
from prefect.logging import disable_run_logger

from pymorize.cmorizer import CMORizer
from pymorize.logging import logger


def test_init(test_config):
    disable_run_logger()  # Turns off Prefect's extra logging layer, for testing
    logger.info(f"Processing {test_config}")
    with open(test_config, "r") as f:
        cfg = yaml.safe_load(f)
    cmorizer = CMORizer.from_dict(cfg)
    # If we get this far, it was possible to construct
    # the object, so this test passes. Meaningless test,
    # but we know that the object is at least constructable:
    assert isinstance(cmorizer, CMORizer)
    # breakpoint()


@pytest.mark.skipif(
    shutil.which("sbatch") is None, reason="sbatch is not available on this host"
)
def test_process(test_config):
    logger.info(f"Processing {test_config}")
    with open(test_config, "r") as f:
        cfg = yaml.safe_load(f)
    cmorizer = CMORizer.from_dict(cfg)
    cmorizer.process()
