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


def test_prefect_can_serialize_rules_with_cache_in_nested_flow(simple_rule):
    @task(cache_policy=TASK_SOURCE + INPUTS)
    def my_step(data, rule):
        return data

    @flow
    def my_flow():
        data_in = None
        data_out = my_step(data_in, simple_rule)
        return data_out

    @flow
    def my_flow_wrapper():
        return my_flow()

    my_flow_wrapper()


def test_prefect_can_serialize_as_pipeline(simple_rule):
    class Pipeline:
        @task(cache_policy=TASK_SOURCE + INPUTS)
        def my_step(self, data, rule):
            return data

        @flow
        def run(self):
            data_in = None
            data_out = self.my_step(data_in, simple_rule)
            return data_out

    class CMORizer:
        def __init__(self, pipelines):
            self.pipelines = pipelines

        @flow
        def run(self):
            results = []
            for pipeline in self.pipelines:
                results.append(pipeline.run())
            return results

    pl = Pipeline()
    cmorizer = CMORizer([pl])
    cmorizer.run()


def test_prefect_can_serialize_as_pipeline_with_cache(simple_rule):
    class Pipeline:
        @task
        def my_step(self, data, rule):
            return data

        @flow
        def run(self):
            data_in = None
            data_out = self.my_step(data_in, simple_rule)
            return data_out

    class CMORizer:
        def __init__(self, pipelines):
            self.pipelines = pipelines

        @flow
        def run(self):
            results = []
            for pipeline in self.pipelines:
                results.append(pipeline.run())
            return results

    pl = Pipeline()
    cmorizer = CMORizer([pl])
    cmorizer.run()


def test_prefect_can_serialize_simplified():
    @task
    def my_step(data, rule):
        return data

    class Pipeline:

        STEPS = [my_step]

        @flow
        def run(self, data, rule_spec):
            for step in self.STEPS:
                data = step(data, rule_spec)
            return data

    class CMORizer:
        def __init__(self, rules, pipelines):
            self.pipelines = pipelines
            self.rules = rules

        @flow
        def run(self):
            results = []
            for rule in self.rules:
                data = None
                for pipeline in rule.pipelines:
                    data = pipeline.run(data, rule)
                results.append(data)
            return results

    class Rule:
        def __init__(self, pipelines):
            self.pipelines = pipelines

    pl = Pipeline()
    rule = Rule([pl])
    cmorizer = CMORizer([rule], [pl])
    cmorizer.run()


def test_prefect_can_serialize_simplified_with_cache():
    @task(cache_policy=TASK_SOURCE + INPUTS)
    def my_step(data, rule):
        return data

    class Pipeline:

        STEPS = [my_step]

        @flow
        def run(self, data, rule_spec):
            for step in self.STEPS:
                data = step(data, rule_spec)
            return data

    class CMORizer:
        def __init__(self, rules, pipelines):
            self.pipelines = pipelines
            self.rules = rules

        @flow
        def run(self):
            results = []
            for rule in self.rules:
                data = None
                for pipeline in rule.pipelines:
                    data = pipeline.run(data, rule)
                results.append(data)
            return results

    class Rule:
        def __init__(self, pipelines):
            self.pipelines = pipelines

    pl = Pipeline()
    rule = Rule([pl])
    cmorizer = CMORizer([rule], [pl])
    cmorizer.run()
