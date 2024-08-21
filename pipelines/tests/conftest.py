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


@pytest.fixture(scope="session")
def pipeline_type(pytestconfig):
    return pytestconfig.getoption("pipeline_type")


@pytest.fixture(scope="session")
def enable_caching(pytestconfig):
    enable_caching_str = pytestconfig.getoption("enable_caching")
    if enable_caching_str is not None:
        return enable_caching_str.lower() == "true"
    return False  # Default to False if not specified
