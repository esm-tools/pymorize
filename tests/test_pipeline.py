from pymorize.pipeline import Pipeline


def test_basic_creation():
    pl = Pipeline()


def test_qualname_creation():
    pl = Pipeline.from_qualname_list(
        ["pymorize.generic.convert_units", "pymorize.generic.set_cmor_metadata"]
    )
