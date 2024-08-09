import os

import pytest

from pymorize.controlled_vocabularies import ControlledVocabularies


@pytest.fixture
def cv_experiment_id():
    current_location = os.path.dirname(os.path.realpath(__file__))
    return ControlledVocabularies(
        [f"{current_location}/../fixtures/CV/CMIP6_experiment_id.json"]
    )


def test_can_create_controlled_vocabularies_instance(cv_experiment_id):
    assert isinstance(cv_experiment_id, ControlledVocabularies)


def test_can_read_experiment_id_json(cv_experiment_id):
    assert "experiment_id" in cv_experiment_id


def test_can_read_start_year_from_experiment_id(cv_experiment_id):
    assert cv_experiment_id["experiment_id"]["highres-future"]["start_year"] == "2015"


def test_can_read_experiment_id_and_source_id_from_directory():
    current_location = os.path.dirname(os.path.realpath(__file__))
    cv = ControlledVocabularies.new_from_dir(f"{current_location}/../fixtures/CV")
    assert cv["experiment_id"]["highres-future"]["start_year"] == "2015"
    assert "experiment_id" in cv
    assert "source_id" in cv
