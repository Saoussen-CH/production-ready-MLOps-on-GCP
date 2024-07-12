# test_lookup_model.py
from kfp.dsl import Model
import pytest
import logging
import components

lookup_model_op = components.lookup_model_op.python_func


def test_lookup_single_model_found(mock_model_list, mock_output_model, tmp_path):
    """
    Assert lookup_model produces expected resource name, and that list method is
    called with the correct arguments.
    """
    mock_path = str(tmp_path / "model")
    mock_model_instance = mock_output_model
    mock_model_instance.resource_name = "my-model-resource-name"
    mock_model_instance.uri = mock_path
    mock_model_list.return_value = [mock_model_instance]

    found_model_resource_name, _ = lookup_model_op(
        model_name="my-model",
        location="us-central1",
        project="my-project-id",
        fail_on_model_not_found=False,
        model=Model(uri=mock_path),
    )

    assert found_model_resource_name == "my-model-resource-name"

    mock_model_list.assert_called_once_with(
        filter='display_name="my-model"',
        location="us-central1",
        project="my-project-id",
    )


def test_lookup_model_no_model_found(mock_model_list, tmp_path, caplog):
    """
    Checks that when there are no models and fail_on_model_found = False,
    lookup_model returns an empty string.
    """
    mock_model_list.return_value = []

    with caplog.at_level(logging.ERROR):
        model_resource_name, training_dataset = lookup_model_op(
            model_name="my-model",
            location="us-central1",
            project="my-project-id",
            fail_on_model_not_found=False,
            model=Model(uri=str(tmp_path / "model")),
        )

    assert model_resource_name == ""
    assert training_dataset == {}
    assert "No model found with name" in caplog.text


def test_lookup_model_fail_on_model_not_found(mock_model_list, tmp_path):
    """
    Checks that when there are no models and fail_on_model_found = True,
    lookup_model raises a RuntimeError.
    """
    mock_model_list.return_value = []

    with pytest.raises(RuntimeError, match="Failed as model was not found"):
        lookup_model_op(
            model_name="my-model",
            location="europe-west4",
            project="my-project-id",
            fail_on_model_not_found=True,
            model=Model(uri=str(tmp_path / "model")),
        )


def test_multiple_models_found(mock_model_list, mock_output_model, tmp_path):
    """
    Checks that when multiple models are found, lookup_model raises a RuntimeError.
    """
    mock_path = str(tmp_path / "model")
    mock_model_instance1 = mock_output_model
    mock_model_instance1.resource_name = "my-model-resource-name-1"
    mock_model_instance1.uri = mock_path

    mock_model_instance2 = mock_output_model
    mock_model_instance2.resource_name = "my-model-resource-name-2"
    mock_model_instance2.uri = mock_path

    mock_model_list.return_value = [mock_model_instance1, mock_model_instance2]

    with pytest.raises(
        RuntimeError, match="Multiple models with name my-model were found."
    ):
        lookup_model_op(
            model_name="my-model",
            location="europe-west4",
            project="my-project-id",
            fail_on_model_not_found=False,
            model=Model(uri=mock_path),
        )
