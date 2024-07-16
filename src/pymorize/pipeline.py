"""
Pipeline of the data processing steps.
"""

from .utils import get_callable_by_name


class Pipeline:
    def __init__(self, *args):
        self.steps = args

    def run(self, data):
        for step in self.steps:
            data = step(data)
        return data

    @classmethod
    def from_list(cls, steps):
        return cls(*steps)

    @classmethod
    def from_qualname_list(cls, qualnames: list):
        return cls.from_list(get_callable_by_name(name) for name in qualnames)


class DefaultPipeline(Pipeline):
    def __init__(self):
        super().__init__(
            get_callable_by_name("pymorize.generic.load_data"),
            get_callable_by_name("extract_feacitures"),
            get_callable_by_name("train"),
            get_callable_by_name("evaluate"),
        )
