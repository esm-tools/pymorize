"""
Integration test that mimics the CLI command for a minimal config
"""

import yaml
from loguru import logger

from pymorize.cmorizer import CMORizer


def test_main():
    # FIXME: This needs to be updated, the path might be incorrect if the test is running
    # from a different location.
    logger.info(f"Processing tests/configs/test_config.yaml")
    with open("tests/configs/test_config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    cmorizer = CMORizer.from_dict(cfg)
    cmorizer.process()
