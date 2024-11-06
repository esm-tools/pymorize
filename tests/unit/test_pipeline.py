from pymorize.pipeline import Pipeline


def test_basic_creation():
    Pipeline()


def test_qualname_creation():
    Pipeline.from_qualname_list(
        ["pymorize.generic.load_data", "pymorize.units.handle_unit_conversion"]
    )
