import asyncio
import functools
import multiprocessing
import os
import time

import dill
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
    return PipelineDB("test_pipeline", keep_db=True)


@pytest.fixture
def step():
    def _step(sleep_time=0):
        time.sleep(sleep_time)

    return _step


@pytest.fixture
def timed_step():
    def step(timer):
        @functools.wraps
        def _step(*args):
            time.sleep(timer)

        return _step

    return step


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
    assert pipeline_db._db == {f"{step.__name__}_{id(step)}": data}


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
    assert step not in pipeline_db


def worker(func, data):
    func = dill.loads(func)
    func(data)


def test_pipeline_can_interrupt(timed_step, data):
    step1 = timed_step(1)
    step2 = timed_step(5)
    step3 = timed_step(1)

    pipeline = Pipeline(step1, step2, step3)
    pipeline_process = multiprocessing.Process(
        target=worker,
        args=(dill.dumps(pipeline.run), data),
    )
    pipeline_process.start()
    time.sleep(2)
    pipeline_process.terminate()

    assert step1 in pipeline._db
    assert step2 in pipeline._db
    assert step3 not in pipeline._db
