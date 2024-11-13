# import pytest
import yaml

from pymorize.cmorizer import CMORizer
from pymorize.logging import logger


def test_process(fesom_2p6_pimesh_esm_tools_config, fesom_2p6_pimesh_esm_tools_data):
    logger.info(f"Processing {fesom_2p6_pimesh_esm_tools_config}")
    with open(fesom_2p6_pimesh_esm_tools_config, "r") as f:
        cfg = yaml.safe_load(f)
    for rule in cfg["rules"]:
        for input in rule["inputs"]:
            input["path"] = input["path"].replace(
                "REPLACE_ME", str(fesom_2p6_pimesh_esm_tools_data)
            )
    cmorizer = CMORizer.from_dict(cfg)
    cmorizer.process()
