"""
Integration test that mimics the CLI command for a minimal config
"""

import shutil

import pytest
import yaml

from pymorize.cmorizer import CMORizer
from pymorize.logging import logger


@pytest.mark.skipif(
    shutil.which("sbatch") is None, reason="sbatch is not available on this host"
)
def test_process(test_config):
    logger.info(f"Processing {test_config}")
    with open(test_config, "r") as f:
        cfg = yaml.safe_load(f)
    cmorizer = CMORizer.from_dict(cfg)
    cmorizer.process()


def test_init(test_config):
    logger.info(f"Processing {test_config}")
    with open(test_config, "r") as f:
        cfg = yaml.safe_load(f)
    cmorizer = CMORizer.from_dict(cfg)
