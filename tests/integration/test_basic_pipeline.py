"""
Integration test that mimics the CLI command for a minimal config
"""

import yaml

from pymorize.cmorizer import CMORizer
from pymorize.logging import logger


def test_process():
    # FIXME: This needs to be updated, the path might be incorrect if the test is running
    # from a different location.
    logger.info("Processing tests/configs/test_config.yaml")
    with open("tests/configs/test_config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    cmorizer = CMORizer.from_dict(cfg)
    cmorizer.process()


def test_init():
    logger.info("Processing tests/configs/test_config.yaml")
    with open("tests/configs/test_config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    cmorizer = CMORizer.from_dict(cfg)
