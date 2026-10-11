import pytest

import pipeline_db


@pytest.fixture
def conn(tmp_path):
    connection = pipeline_db.connect(tmp_path / "test.sqlite")
    yield connection
    connection.close()
