import os

import pytest

from pymorize.pipeline import Pipeline, PipelineDB


def test_basic_creation():
    Pipeline()


def test_qualname_creation():
    Pipeline.from_qualname_list(
        ["pymorize.generic.convert_units", "pymorize.generic.set_cmor_metadata"]
    )


@pytest.fixture
def pipeline_db():
    return PipelineDB("test_pipeline")


@pytest.fixture
def step():
    return lambda: None


@pytest.fixture
def data():
    return {"key": "value"}


def test_pipeline_db_init(pipeline_db):
    assert pipeline_db._db == {}


def test_pipeline_db_save_and_load(pipeline_db, step, data):
    pipeline_db.create(step, data)
    pipeline_db.save()
    assert os.path.exists(pipeline_db._db_file)
    pipeline_db._db = {}
    pipeline_db.load()
    assert pipeline_db._db == {step.__name__: data}


def test_create_and_read(pipeline_db, step, data):
    pipeline_db.create(step, data)
    assert pipeline_db.read(step) == data


def test_update(pipeline_db, step, data):
    pipeline_db.create(step, data)
    pipeline_db.update(step, {"new_key": "new_value"})
    assert pipeline_db.read(step) == {"key": "value", "new_key": "new_value"}


def test_delete(pipeline_db, step, data):
    pipeline_db.create(step, data)
    pipeline_db.delete(step)
    assert pipeline_db.read(step) is None
