import pytest
from kfp.dsl import Model
from google.cloud.aiplatform_v1beta1.types import JobState

import components

model_batch_predict_op = components.model_batch_predict_op.python_func

SKEW_THRESHOLD = {"defaultSkewThreshold": {"value": 0.001}}
TRAIN_DATASET = {
    "gcsSource": {"uris": ["gs://file.csv"]},
    "dataFormat": "csv",
    "targetField": "col",
}


@pytest.mark.parametrize(
    (
        "source_format, destination_format, source_uri, monitoring_training_dataset, "
        "monitoring_alert_email_addresses, monitoring_skew_config"
    ),
    [
        ("bigquery", "bigquery", "bq://a.b.c", None, None, None),
        ("csv", "csv", '["gs://file.csv"]', None, None, None),
        ("csv", "csv", '["gs://file.csv"]', TRAIN_DATASET, [], SKEW_THRESHOLD),
        ("csv", "csv", '["gs://file.csv"]', TRAIN_DATASET, ["a@b.com"], SKEW_THRESHOLD),
    ],
)
def test_model_batch_predict_successful(
    mock_create_batch_prediction_job,
    mock_get_batch_prediction_job,
    tmp_path,
    source_format,
    destination_format,
    source_uri,
    monitoring_training_dataset,
    monitoring_alert_email_addresses,
    monitoring_skew_config,
):
    """
    Test model_batch_predict_op function for a successful batch
    prediction job creation with different parameter configurations.
    """
    mock_create_batch_prediction_job.return_value.name = (
        "projects/my-project/locations/us-central1/batchPredictionJobs/123456789"
    )
    mock_get_batch_prediction_job.return_value.state = JobState.JOB_STATE_SUCCEEDED

    job_display_name = "test-batch-prediction-job"
    location = "us-central1"
    project = "my-project"
    destination_uri = "gs://destination-uri"
    gcp_resources_path = str(tmp_path / "gcp_resources.json")

    (gcp_resources,) = model_batch_predict_op(
        model=Model(
            uri="gs://model-uri", metadata={"resourceName": "model-resource-name"}
        ),
        gcp_resources=gcp_resources_path,
        job_display_name=job_display_name,
        location=location,
        project=project,
        source_uri=source_uri,
        destination_uri=destination_uri,
        source_format=source_format,
        destination_format=destination_format,
        monitoring_training_dataset=monitoring_training_dataset,
        monitoring_alert_email_addresses=monitoring_alert_email_addresses,
        monitoring_skew_config=monitoring_skew_config,
    )

    assert gcp_resources is not None
    with open(gcp_resources_path, "r") as f:
        content = f.read()
        assert "BatchPredictionJob" in content
        assert (
            "projects/my-project/locations/us-central1/batchPredictionJobs/123456789"
            in content
        )
    mock_create_batch_prediction_job.assert_called_once()
    mock_get_batch_prediction_job.assert_called_once()


def test_model_batch_predict_failed(
    mock_create_batch_prediction_job, mock_get_batch_prediction_job, tmp_path
):
    """
    Test the model_batch_predict_op function for a failed batch prediction job creation.
    """
    mock_create_batch_prediction_job.return_value.name = (
        "projects/my-project/locations/us-central1/batchPredictionJobs/123456789"
    )
    mock_get_batch_prediction_job.return_value.state = JobState.JOB_STATE_FAILED

    job_display_name = "test-batch-prediction-job"
    location = "us-central1"
    project = "my-project"
    source_uri = "gs://source-uri"
    destination_uri = "gs://destination-uri"
    source_format = "jsonl"
    destination_format = "jsonl"
    gcp_resources_path = str(tmp_path / "gcp_resources.json")

    with pytest.raises(RuntimeError):
        model_batch_predict_op(
            model=Model(
                uri="gs://model-uri", metadata={"resourceName": "model-resource-name"}
            ),
            gcp_resources=gcp_resources_path,
            job_display_name=job_display_name,
            location=location,
            project=project,
            source_uri=source_uri,
            destination_uri=destination_uri,
            source_format=source_format,
            destination_format=destination_format,
            machine_type="n1-standard-2",
            starting_replica_count=1,
            max_replica_count=1,
        )
