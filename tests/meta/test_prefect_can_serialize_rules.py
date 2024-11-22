from prefect import flow, task
from prefect.cache_policies import INPUTS, TASK_SOURCE


def test_prefect_can_serialize_rules(simple_rule):

    @task
    def my_step(data, rule):
        return data

    @flow
    def my_flow():
        data_in = None
        data_out = my_step(data_in, simple_rule)
        return data_out

    my_flow()


def test_prefect_can_serialize_rules_with_cache(simple_rule):

    @task(cache_policy=TASK_SOURCE + INPUTS)
    def my_step(data, rule):
        return data

    @flow
    def my_flow():
        data_in = None
        data_out = my_step(data_in, simple_rule)
        return data_out

    my_flow()
