import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--pipeline_type",
        type=str,
        help="choose the pipeline type <training|prediction> to run e2e tests for",
        default=None,
    )


@pytest.fixture(scope="session")
def pipeline_type(pytestconfig):
    return pytestconfig.getoption("pipeline_type")
