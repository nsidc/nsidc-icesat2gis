from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
TEST_DATA_DIR = _THIS_DIR / "data"


@pytest.fixture
def atl08_test_filepath() -> Path:
    test_data_path = TEST_DATA_DIR / "test_atl08.h5"

    return test_data_path
