# import pytest
import yaml

from pymorize.cmorizer import CMORizer
from pymorize.logging import logger


def test_process(pi_uxarray_config, pi_uxarray_data):
    logger.info(f"Processing {pi_uxarray_config}")
    with open(pi_uxarray_config, "r") as f:
        cfg = yaml.safe_load(f)
    for rule in cfg["rules"]:
        for input in rule["inputs"]:
            input["path"] = input["path"].replace("REPLACE_ME", str(pi_uxarray_data))
    cmorizer = CMORizer.from_dict(cfg)
    cmorizer.process()
