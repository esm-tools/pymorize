import asyncio
import functools
import multiprocessing
import os
import shutil
import time

import dill
import pytest

from pymorize.pipeline import Pipeline, PipelineDB, TestingPipeline


def test_basic_creation():
    Pipeline()


def test_qualname_creation():
    Pipeline.from_qualname_list(
        ["pymorize.generic.load_data", "pymorize.units.handle_unit_conversion"]
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
        @functools.wraps(step)
        def _step(*args):
            time.sleep(timer)

        return _step

    return step


@pytest.fixture
def fake_pipeline_data():
    return {"status": "scheduled", "key": "value", "key2": "value2"}


def test_pipeline_db_init(pipeline_db):
    assert pipeline_db._db == {}


def test_pipeline_db_save_and_load(pipeline_db, step, fake_pipeline_data):
    pipeline_db.create(step, fake_pipeline_data)
    pipeline_db.save()
    assert os.path.exists(pipeline_db._db_file)
    pipeline_db._db = {}
    pipeline_db.load()
    assert pipeline_db._db == {f"{step.__name__}_{id(step)}": fake_pipeline_data}


def test_create_and_read(pipeline_db, step, fake_pipeline_data):
    pipeline_db.create(step, fake_pipeline_data)
    assert pipeline_db.read(step) == fake_pipeline_data


def test_update(pipeline_db, step, fake_pipeline_data):
    pipeline_db.create(step, fake_pipeline_data)
    pipeline_db.update(step, {"new_key": "new_value"})
    assert pipeline_db.read(step) == {
        "status": "scheduled",
        "key": "value",
        "key2": "value2",
        "new_key": "new_value",
    }


def test_delete(pipeline_db, step, fake_pipeline_data):
    pipeline_db.create(step, fake_pipeline_data)
    pipeline_db.delete(step)
    assert step not in pipeline_db


def worker(func, *args):
    func = dill.loads(func)
    func(*args)


def test_pipeline_can_run(timed_step, fake_pipeline_data):
    step1 = timed_step(0.1)
    step2 = timed_step(0.5)
    step3 = timed_step(0.1)

    pipeline = Pipeline(step1, step2, step3)
    pipeline_process = multiprocessing.Process(
        target=worker,
        args=(dill.dumps(pipeline.run), fake_pipeline_data),
    )
    pipeline_process.start()


# FIXME: I still need to figure out how to handle interrupt in testing
@pytest.mark.skip
def test_pipeline_can_interrupt(timed_step, fake_pipeline_data):
    step1 = timed_step(0.1)
    step2 = timed_step(0.5)
    step3 = timed_step(0.1)

    pipeline = Pipeline(step1, step2, step3)
    pipeline_process = multiprocessing.Process(
        target=worker,
        args=(dill.dumps(pipeline.run), fake_pipeline_data),
    )
    pipeline_process.start()
    time.sleep(0.2)
    pipeline_process.terminate()

    assert step1 in pipeline._db
    assert step2 in pipeline._db
    assert step3 not in pipeline._db


# FIXME: I still need to figure out how to handle interrupt in testing
@pytest.mark.skip
def test_pipeline_can_interrupt_and_restart(timed_step, fake_pipeline_data):
    step1 = timed_step(0.1)
    step2 = timed_step(0.5)
    step3 = timed_step(0.1)

    pipeline = Pipeline(step1, step2, step3)
    pipeline_process = multiprocessing.Process(
        target=worker,
        args=(dill.dumps(pipeline.run), fake_pipeline_data),
    )
    pipeline_process.start()
    time.sleep(0.2)
    pipeline_process.terminate()

    assert step1 in pipeline._d
    assert step2 in pipeline._db
    assert step3 not in pipeline._db

    pipeline_process.start()
    assert step1 in pipeline._db
    assert step2 in pipeline._db
    assert step3 in pipeline._db


@pytest.mark.skipif(
    shutil.which("sbatch") is None, reason="sbatch is not available on this host"
)
def test_dummy_pipeline():
    pl = TestingPipeline()
    data = pl.run({}, {})
