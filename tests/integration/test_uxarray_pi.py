# import pytest
import yaml

from pymorize.cmorizer import CMORizer
from pymorize.logging import logger


def test_process(test_uxarray_config, pi_uxarray_data):
    logger.info(f"Processing {test_uxarray_config}")
    with open(test_uxarray_config, "r") as f:
        cfg = yaml.safe_load(f)
    for rule in cfg.rules:
        for input in rule["inputs"]:
            input["path"] = input["path"].replace("REPLACE_ME", pi_uxarray_data)

    cmorizer = CMORizer.from_dict(test_uxarray_config)
    cmorizer.process()
