import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--pipeline_type",
        type=str,
        help="Choose the pipeline type <training|prediction> to run e2e tests for",
        default=None,
    )
    parser.addoption(
        "--enable_caching",
        type=str,
        help="Whether to enable or disable caching for all pipeline steps",
        default="false",  # Default should be 'false' if not set
    )
    parser.addoption(
        "--timestamp",
        type=str,
        help="Specify the timestamp for the pipeline in ISO 8601 format",
        default="",  # Default should be an empty string if not set
    )
    parser.addoption(
        "--use_latest_data",
        type=str,
        help="Whether to use the latest data or a fixed timestamp",
        default="true",  # Default should be 'true' if not set
    )


@pytest.fixture(scope="session")
def pipeline_type(pytestconfig):
    return pytestconfig.getoption("pipeline_type")


@pytest.fixture(scope="session")
def enable_caching(pytestconfig):
    enable_caching_str = pytestconfig.getoption("enable_caching")
    if enable_caching_str is not None:
        return enable_caching_str.lower() == "true"
    return False  # Default to False if not specified


@pytest.fixture(scope="session")
def timestamp(pytestconfig):
    return pytestconfig.getoption("timestamp")


@pytest.fixture(scope="session")
def use_latest_data(pytestconfig):
    use_latest_data_str = pytestconfig.getoption("use_latest_data")
    if use_latest_data_str is not None:
        return use_latest_data_str.lower() == "true"
    return True  # Default to True if not specified
