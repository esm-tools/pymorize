import pickle
import types

import yaml
from prefect import flow, task

from pymorize.cmorizer import CMORizer
from pymorize.data_request.collection import CMIP6DataRequest
from pymorize.rule import Rule

cmip6_dr = CMIP6DataRequest.from_git()


rule_spec = {
    "name": "paul_example_rule",
    "description": "You can put some text here",
    "inputs": [
        {
            "path": "/work/ba1103/a270073/out/awicm-1.0-recom/awi-esm-1-1-lr_kh800/piControl/outdata/fesom",
            "pattern": "CO2f_fesom_.*nc",
        }
    ],
    "cmor_variable": "fgco2",
    "model_variable": "CO2f",
    "output_directory": ".",
    "variant_label": "r1i1p1f1",
    "experiment_id": "piControl",
    "source_id": "ocean",
    "pipelines": ["default"],
}


my_rule = Rule.from_dict(rule_spec)
my_rule.data_request_variable = cmip6_dr.variables["Omon.fgco2"]


def find_generators(obj, path="root"):
    """Recursively search for generators in an object's tree."""
    if isinstance(obj, types.GeneratorType):
        print(f"Generator found at: {path}")
        return

    # Check if the object has a dictionary of attributes
    if hasattr(obj, "__dict__"):
        for attr, value in vars(obj).items():
            find_generators(value, path=f"{path}.{attr}")

    # Check if the object is iterable (like a list or dict) but not a string
    elif isinstance(obj, (list, tuple, set, dict)):
        if isinstance(obj, dict):
            for key, value in obj.items():
                find_generators(value, path=f"{path}[{repr(key)}]")
        else:
            for idx, item in enumerate(obj):
                find_generators(item, path=f"{path}[{idx}]")


class Example:
    def __init__(self):
        self.attr1 = [i for i in range(10)]  # List comprehension (not a generator)
        self.attr2 = (i for i in range(10))  # Generator


obj = Example()

with open("../examples/sample.yaml", "r") as f:
    cmor_config = yaml.safe_load(f)
    my_cmorizer = CMORizer.from_dict(cmor_config)

my_rule2 = my_cmorizer.rules[0]

# Search for generators
find_generators(obj)
find_generators(my_rule)

# Save the rule to a file
with open("my_rule.pkl", "wb") as f:
    pickle.dump(my_rule2, f)
print("Rule saved to my_rule.pkl")


@flow
def parent_flow():
    rval = sub_flow(my_cmorizer, my_rule2)
    return rval


@flow
def sub_flow(cmorizer, rule):
    data = None
    return my_step(data, rule)


@task
def my_step(data, rule):
    print(f"Step: {data}, {rule}")
    return data


parent_flow()
