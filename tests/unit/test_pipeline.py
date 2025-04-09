from pymorize.core.pipeline import Pipeline


def test_basic_creation():
    Pipeline()


def test_qualname_creation():
    Pipeline.from_qualname_list(
        [
            "pymorize.std_lib.generic.load_data",
            "pymorize.std_lib.units.handle_unit_conversion",
        ]
    )
