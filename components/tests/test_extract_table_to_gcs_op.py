import pytest
from unittest.mock import MagicMock
from google.cloud.bigquery.job import ExtractJob

import components

extract_table_to_gcs_op = components.extract_table_to_gcs_op.python_func


def test_extract_table_to_gcs_op(mocker):
    # Mock the inputs
    mock_bq_table = MagicMock()
    mock_bq_table.metadata = {
        "projectId": "test-project",
        "datasetId": "test-dataset",
        "tableId": "test-table",
    }  # noqa
    mock_dataset = MagicMock()
    mock_dataset.uri = "gs://test-bucket/test-file"

    # Mock the BigQuery client and table
    mock_extract_job = MagicMock(spec=ExtractJob)

    # Use mocker for convenient patching
    mock_client = mocker.patch("google.cloud.bigquery.client.Client")
    mock_table = mocker.patch("google.cloud.bigquery.table.Table")
    mock_table.return_value = mock_bq_table
    mock_client.return_value.extract_table.return_value = mock_extract_job

    extract_table_to_gcs_op(mock_bq_table, mock_dataset, "US")

    # Assert interactions with mocked objects
    mock_client.assert_called_once_with(project="test-project", location="US")
    mock_client.return_value.extract_table.assert_called_once_with(
        mock_bq_table, "gs://test-bucket/test-file"
    )
    mock_extract_job.result.assert_called_once_with()


def test_extract_table_to_gcs_op_handles_errors(mocker):
    # Mock the inputs
    mock_bq_table = MagicMock()
    mock_bq_table.metadata = {
        "projectId": "test-project",
        "datasetId": "test-dataset",
        "tableId": "test-table",
    }

    # Mock the output
    mock_dataset = MagicMock()
    mock_dataset.uri = "gs://test-bucket/test-file"

    # Mock the BigQuery client
    mock_client = mocker.patch("google.cloud.bigquery.client.Client")
    mock_client.return_value = MagicMock()

    # Mock the extract job to raise an exception
    mock_extract_job = MagicMock(spec=ExtractJob)
    mock_extract_job.result.side_effect = Exception("Test exception")
    mock_client.return_value.extract_table.return_value = mock_extract_job

    # Call the function to test
    with pytest.raises(Exception) as exc_info:
        extract_table_to_gcs_op(mock_bq_table, mock_dataset, "US")

    # Assert that the function re-raised the exception from the extract job
    assert str(exc_info.value) == "Test exception"
