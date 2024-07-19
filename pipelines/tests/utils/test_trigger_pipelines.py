import os
from pipelines.utils.trigger_pipeline import trigger_pipeline


def test_trigger_pipeline(mocker):
    # Set up mock objects
    mock_pipeline_job = mocker.patch(
        "google.cloud.aiplatform.pipeline_jobs.PipelineJob"
    )
    mock_pipeline_job_instance = mocker.Mock()
    mock_pipeline_job_instance.run.return_value = None
    mock_pipeline_job_instance.wait.return_value = None
    mock_pipeline_job.return_value = mock_pipeline_job_instance

    mock_init = mocker.patch("google.cloud.aiplatform.init")

    # Set up environment variables
    os.environ["VERTEX_PROJECT_ID"] = "test-project"
    os.environ["VERTEX_LOCATION"] = "us-central1"
    os.environ["BUCKET_URI"] = "gs://test-bucket"

    # Call the function with test arguments
    template_path = "gs://test-bucket/pipeline.yaml"
    display_name = "test-pipeline"
    pipeline_type = "training"
    result = trigger_pipeline(template_path, display_name, pipeline_type)

    # Assert that the function returned the expected object
    assert result == mock_pipeline_job_instance

    # Assert that aiplatform.init was called with the correct arguments
    mock_init.assert_called_once_with(project="test-project", location="us-central1")

    # Assert that PipelineJob was called with the correct arguments
    expected_params = {
        "project": "test-project",
        "location": "us-central1",
        "training_job_display_name": "test-pipeline-training-job",
        "base_output_dir": "gs://test-bucket",
    }
    mock_pipeline_job.assert_called_once_with(
        display_name="test-pipeline",
        template_path="gs://test-bucket/pipeline.yaml",
        parameter_values=expected_params,
        pipeline_root="gs://test-bucket",
        enable_caching=True,
        location="us-central1",
    )

    # Assert that run and wait were called on the PipelineJob instance
    mock_pipeline_job_instance.run.assert_called_once()
    mock_pipeline_job_instance.wait.assert_called_once()
