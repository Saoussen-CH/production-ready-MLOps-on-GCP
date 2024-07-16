from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

import components

get_custom_job_results_op = components.get_custom_job_results_op.python_func


def test_get_custom_job_results_op(mocker):
    # Mock the inputs
    project = "test-project"
    location = "us-central1"
    job_resource = '{"resources": [{"resource_uri": "projects/test-project/locations/us-central1/customJobs/12345"}]}'  # noqa
    model_uri = "gs://test-bucket/test-model"
    # metrics_uri = "gs://test-bucket/test-metrics.json"

    # Mock the outputs
    model = MagicMock()
    model.uri = model_uri
    metrics = MagicMock()
    metrics.path = "/tmp/metrics.json"
    metrics.log_metric = MagicMock()

    # Mock the aiplatform.init method
    mock_init = mocker.patch("google.cloud.aiplatform.init")

    # Mock the CustomJob.get method
    mock_custom_job_get = mocker.patch("google.cloud.aiplatform.CustomJob.get")

    # Mock the job resource return value
    mock_custom_job_instance = MagicMock()
    mock_custom_job_instance.gca_resource.job_spec.base_output_directory.output_uri_prefix = (  # noqa
        "gs://test-bucket/test-job"
    )
    mock_custom_job_get.return_value = mock_custom_job_instance

    # Mock the json.load method
    with patch("builtins.open", mock_open(read_data='{"rmse": 0.8}')):
        # Mock the shutil.copytree method
        mock_copytree = mocker.patch("shutil.copytree")

        # Mock the shutil.rmtree method
        mock_rmtree = mocker.patch("shutil.rmtree")

        # Call the function to test
        get_custom_job_results_op(
            project=project,
            location=location,
            job_resource=job_resource,
            model=model,
            metrics=metrics,
        )

        # Assert that the aiplatform client was initialized with the
        # correct project and location
        mock_init.assert_called_once_with(project=project, location=location)

        # Assert that the CustomJob.get method was called with the correct arguments
        mock_custom_job_get.assert_called_once_with(
            "projects/test-project/locations/us-central1/customJobs/12345"
        )

        # Convert the URIs from gs to gcs
        job_base_dir_fuse = mock_custom_job_instance.gca_resource.job_spec.base_output_directory.output_uri_prefix.replace(  # noqa
            "gs://", "/gcs/"
        )
        model_uri_fuse = model.uri.replace("gs://", "/gcs/")

        # Assert that the shutil.copytree method was called correctly
        mock_copytree.assert_called_once_with(
            f"{job_base_dir_fuse}/model",
            Path(
                model_uri_fuse
            ),  # Add test-model to destination path,  # Convert PosixPath to string
            dirs_exist_ok=True,
        )

        # Assert that the json.load method was called correctly
        open.assert_any_call(f"{job_base_dir_fuse}/metrics/metrics.json")
        metrics.log_metric.assert_any_call("rmse", 0.8)

        # Assert that the shutil.rmtree method was called correctly
        mock_rmtree.assert_any_call(f"{job_base_dir_fuse}/model")
