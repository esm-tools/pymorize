import pytest
import yaml

from pymorize.cmorizer import CMORizer
from pymorize.logging import logger
from pymorize.pipeline import DefaultPipeline

STEPS = DefaultPipeline.STEPS
PROGRESSIVE_STEPS = [STEPS[: i + 1] for i in range(len(STEPS))]


# There is a segfault somewhere in the code, so I'd like to find out where it is...
@pytest.mark.parametrize("steps", PROGRESSIVE_STEPS)
def test_process_progressive_pipeline(
    fesom_2p6_pimesh_esm_tools_config, fesom_2p6_pimesh_esm_tools_data, steps
):
    logger.info(f"Processing {fesom_2p6_pimesh_esm_tools_config} with {steps}")
    with open(fesom_2p6_pimesh_esm_tools_config, "r") as f:
        cfg = yaml.safe_load(f)
    if "pipelines" not in cfg:
        cfg["pipelines"] = []
    for rule in cfg["rules"]:
        for input in rule["inputs"]:
            input["path"] = input["path"].replace(
                "REPLACE_ME", str(fesom_2p6_pimesh_esm_tools_data)
            )
        rule["pipelines"] = ["default"]
    cfg["pipelines"].append("name": "default", "steps": []})
    pipeline = cfg["pipelines"][0]
    pipeline["steps"] = steps
    cmorizer = CMORizer.from_dict(cfg)
    cmorizer.process()


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
