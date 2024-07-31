import os
from unittest import mock

import pytest


@pytest.fixture
def env(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def env_empty():
    with mock.patch.dict(os.environ, {}, clear=True):
        yield
