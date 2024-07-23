from pipelines.utils.upload_pipeline import upload_pipeline
from os import environ as env


def test_upload_pipeline(mocker):
    # Set up test inputs
    yaml = "path/to/template.yaml"
    dest = "https://us-cental1-kfp.pkg.dev/dummy-project/dummy-repo"
    input_tags = ["dummy_tag1", "dummy_tag2"]

    # Mock environment variables
    mocker.patch.dict(
        env,
        {
            "VERTEX_PROJECT_ID": "test-project-id",
            "VERTEX_LOCATION": "test-location",
            "KFP_TEMPLATE_AR": dest,
        },
    )

    # Mock RegistryClient
    mock_client = mocker.patch("pipelines.utils.upload_pipeline.RegistryClient")
    mock_instance = mock_client.return_value
    mock_instance.upload_pipeline.return_value = ("test-package", "v1")

    # Call the function
    result = upload_pipeline(file_name=yaml, tags=input_tags)

    # Assertions
    mock_client.assert_called_with(host=dest)
    mock_instance.upload_pipeline.assert_called_with(
        file_name=yaml,
        tags=input_tags,
        extra_headers={
            "description": "This is Kubeflow pipeline template for taxifare."
        },
    )
    assert result == ("test-package", "v1")
