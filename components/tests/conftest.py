import pytest
import kfp.dsl
import json


@pytest.fixture(autouse=True)
def mock_kfp_artifact(mocker):
    """
    This fixture mocks the Artifact object (and thus any derived
    classes i.e Dataset, Model, etc.)
    to return the URI as the path.

    Unit tests set the URI of artifacts, however, KFP components use Artifact.path to
    retrieve paths to files. If a URI doesn't start with gs:// or minio:// or s3://,
    the path with be None. This behaviour is avoided by mocking the Artifact._get_path
    method.

    Args:
        mocker: Used to patch the _get_path method in `kfp.dsl.Artifact`.

    Returns:
        None
    """

    def _get_path(self):
        return self.uri

    # mock the _get_path method of Artifact which is used by the property path
    mocker.patch.object(kfp.dsl.Artifact, "_get_path", _get_path)


@pytest.fixture
def mock_output_model(mocker):
    return mocker.MagicMock()


@pytest.fixture
def mock_model_list(mocker):
    return mocker.patch("google.cloud.aiplatform.Model.list")


@pytest.fixture
def mock_job_service_client(mocker):
    return mocker.patch(
        "google.cloud.aiplatform_v1beta1.services.job_service.JobServiceClient"
    )


@pytest.fixture
def mock_create_batch_prediction_job(mock_job_service_client):
    return mock_job_service_client.return_value.create_batch_prediction_job


@pytest.fixture
def mock_get_batch_prediction_job(mock_job_service_client):
    return mock_job_service_client.return_value.get_batch_prediction_job


@pytest.fixture
def mock_model_class(mocker):
    return mocker.patch("google.cloud.aiplatform.Model")


@pytest.fixture
def mock_model(tmp_path):
    return type(
        "MockModel",
        (object,),
        {
            "uri": str(tmp_path / "model-uri"),
            "metadata": {"resourceName": "model-resource-name"},
        },
    )()


@pytest.fixture
def mock_dataset(tmp_path):
    return type("MockDataset", (object,), {"uri": str(tmp_path / "test-data-uri")})()


@pytest.fixture
def mock_metrics(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    metrics = {"problemType": "classification", "accuracy": 0.9}
    with open(metrics_path, "w") as f:
        json.dump(metrics, f)
    return type("MockMetrics", (object,), {"path": str(metrics_path)})()


@pytest.fixture
def mock_model_service_client(mocker):
    return mocker.patch("google.cloud.aiplatform_v1.ModelServiceClient")
