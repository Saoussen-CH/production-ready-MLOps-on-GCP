import json
import logging
from kfp.dsl import Dataset, Metrics, Model
from unittest import mock
from google.protobuf.json_format import ParseDict
from google.cloud.aiplatform_v1 import ModelEvaluation
from google_cloud_pipeline_components.types.artifact_types import VertexModel

import components

upload_model = components.upload_best_model_op.python_func


def test_model_upload_no_champion(
    mock_model_class, mock_model_service_client, caplog, tmp_path
):
    caplog.set_level(logging.INFO)

    metrics_json = json.dumps(
        {
            "problemType": "regression",
            "auc": 0.4,
            "accuracy": 0.80,
        }
    )
    metrics_file_path = tmp_path / "metrics.json"
    metrics_file_path.write_text(metrics_json)

    mock_model_class.list.return_value = []

    model = Model(uri="dummy-model-uri")
    serving_container_image = "dummy_image:latest"
    model_name = "dummy-model-name"
    model_description = "dummy model_description"
    vertex_model = VertexModel.create(
        name=model_name, uri="chall_uri", model_resource_name="chall_resource_name"
    )
    project = "dummy-project"
    location = "dummy-location"
    model_evaluation = Metrics(uri="")
    model_evaluation.path = str(metrics_file_path)
    eval_metric = "auc"
    eval_lower_is_better = False

    pipeline_job_id = "dummy-pipeline-job-id"
    test_dataset = Dataset(uri="test-dataset-uri")
    evaluation_name = "dummy evaluation name"

    upload_model(
        model=model,
        model_description=model_description,
        serving_container_image=serving_container_image,
        vertex_model=vertex_model,
        project=project,
        location=location,
        model_eval_metrics=model_evaluation,
        eval_metric=eval_metric,
        eval_lower_is_better=eval_lower_is_better,
        model_name=model_name,
        pipeline_job_id=pipeline_job_id,
        test_data=test_dataset,
        evaluation_name=evaluation_name,
    )

    # Check that model lookup is performed, and no existing model is found
    mock_model_class.list.assert_called_once_with(
        filter=f'display_name="{model_name}"',
        location=location,
        project=project,
    )
    assert "found 0 models" in caplog.text

    # Check no model comparison occurs
    assert "wins" not in caplog.text

    # Check model upload call
    mock_model_class.upload.assert_called_once_with(
        display_name=model_name,
        description=model_description,
        artifact_uri="dummy-model-uri",
        serving_container_image_uri=serving_container_image,
        parent_model=None,
        is_default_version=True,
    )

    # check model output URI
    assert vertex_model.uri == f"https://{location}-aiplatform.googleapis.com/v1/" + (
        str(mock_model_class.upload.return_value.versioned_resource_name)
    )

    # check evaluation import
    mock_model_service_client.return_value.import_model_evaluation.assert_called_once_with(  # noqa
        parent=mock_model_class.upload.return_value.versioned_resource_name,
        model_evaluation=mock.ANY,
    )


def test_model_upload_challenger_wins(
    mock_model_class, mock_model_service_client, caplog, tmp_path, mocker
):
    caplog.set_level(logging.INFO)

    metrics_json = json.dumps(
        {
            "problemType": "regression",
            "auc": 0.4,
            "accuracy": 0.80,
        }
    )
    metrics_file_path = tmp_path / "metrics.json"
    metrics_file_path.write_text(metrics_json)

    # create mock champion model
    mock_champion_model = mocker.Mock()
    mock_champion_model.version_id = "123"
    dummy_champion_eval = ModelEvaluation()
    dummy_champion_metrics = {
        "auc": 0.2,
        "f1": 0.7,
    }
    message_dict = {
        "displayName": "Previously imported evaluation",
        "metricsSchemaUri": "gs://google-cloud-aiplatform/schema/modelevaluation/regression_metrics_1.0.0.yaml",  # noqa
        "metrics": dummy_champion_metrics,
        "metadata": {
            "pipeline_job_id": "dummy-pipeline-id",
            "evaluation_dataset_type": "gcs",
            "evaluation_dataset_path": ["dummy-gcs-uri"],
        },
    }
    ParseDict(message_dict, dummy_champion_eval._pb)
    mock_champion_model.get_model_evaluation.return_value._gca_resource = (
        dummy_champion_eval
    )
    mock_champion_model.resource_name = "dummy-champion-resource-name"
    mock_model_class.list.return_value = [mock_champion_model]

    # create mock challenger model
    model = Model(uri="dummy-model-uri")
    serving_container_image = "dummy_image:latest"
    model_name = "dummy-model-name"
    model_description = "dummy model_description"
    vertex_model = VertexModel.create(
        name=model_name, uri="chall_uri", model_resource_name="chall_resource_name"
    )
    project = "dummy-project"
    location = "dummy-location"
    model_evaluation = Metrics(uri="")
    model_evaluation.path = str(metrics_file_path)
    eval_metric = "auc"
    eval_lower_is_better = False

    pipeline_job_id = "dummy-pipeline-job-id"
    test_dataset = Dataset(uri="test-dataset-uri")
    evaluation_name = "dummy evaluation name"

    upload_model(
        model=model,
        model_description=model_description,
        serving_container_image=serving_container_image,
        vertex_model=vertex_model,
        project=project,
        location=location,
        model_eval_metrics=model_evaluation,
        eval_metric=eval_metric,
        eval_lower_is_better=eval_lower_is_better,
        model_name=model_name,
        pipeline_job_id=pipeline_job_id,
        test_data=test_dataset,
        evaluation_name=evaluation_name,
    )

    # Check that model lookup is performed, and no existing model is found
    mock_model_class.list.assert_called_once_with(
        filter=f'display_name="{model_name}"',
        location=location,
        project=project,
    )
    assert "is being challenged by new model" in caplog.text

    # Check challenger wins in model comparison
    assert "Challenger wins!" in caplog.text

    # Check model upload call
    mock_model_class.upload.assert_called_once_with(
        display_name=model_name,
        description=model_description,
        artifact_uri="dummy-model-uri",
        serving_container_image_uri=serving_container_image,
        parent_model=mock_champion_model.resource_name,
        is_default_version=True,
    )

    # check model output URI
    assert vertex_model.uri == f"https://{location}-aiplatform.googleapis.com/v1/" + (
        str(mock_model_class.upload.return_value.versioned_resource_name)
    )

    # check evaluation import
    mock_model_service_client.return_value.import_model_evaluation.assert_called_once_with(  # noqa
        parent=mock_model_class.upload.return_value.versioned_resource_name,
        model_evaluation=mock.ANY,
    )


def test_model_upload_champion_wins(
    mock_model_class, mock_model_service_client, caplog, tmp_path, mocker
):
    caplog.set_level(logging.INFO)

    metrics_json = json.dumps(
        {
            "problemType": "regression",
            "auc": 0.4,
            "accuracy": 0.80,
        }
    )
    metrics_file_path = tmp_path / "metrics.json"
    metrics_file_path.write_text(metrics_json)

    # Create mock champion model
    mock_champion_model = mocker.Mock()
    mock_champion_model.version_id = "123"
    dummy_champion_eval = ModelEvaluation()
    dummy_champion_metrics = {
        "auc": 0.8,
        "f1": 0.7,
    }
    message_dict = {
        "displayName": "Previously imported evaluation",
        "metricsSchemaUri": "gs://google-cloud-aiplatform/schema/modelevaluation/regression_metrics_1.0.0.yaml",  # noqa
        "metrics": dummy_champion_metrics,
        "metadata": {
            "pipeline_job_id": "dummy-pipeline-id",
            "evaluation_dataset_type": "gcs",
            "evaluation_dataset_path": ["dummy-gcs-uri"],
        },
    }
    ParseDict(message_dict, dummy_champion_eval._pb)
    mock_champion_model.get_model_evaluation.return_value._gca_resource = (
        dummy_champion_eval
    )
    mock_champion_model.resource_name = "dummy-champion-resource-name"
    mock_model_class.list.return_value = [mock_champion_model]

    # Create mock challenger model
    model = Model(uri="dummy-model-uri")
    serving_container_image = "dummy_image:latest"
    model_name = "dummy-model-name"
    model_description = "dummy model_description"
    vertex_model = VertexModel.create(
        name=model_name, uri="chall_uri", model_resource_name="chall_resource_name"
    )
    project = "dummy-project"
    location = "dummy-location"
    model_evaluation = Metrics(uri="")
    model_evaluation.path = str(metrics_file_path)
    eval_metric = "auc"
    eval_lower_is_better = False

    pipeline_job_id = "dummy-pipeline-job-id"
    test_dataset = Dataset(uri="test-dataset-uri")
    evaluation_name = "dummy evaluation name"

    upload_model(
        model=model,
        model_description=model_description,
        serving_container_image=serving_container_image,
        vertex_model=vertex_model,
        project=project,
        location=location,
        model_eval_metrics=model_evaluation,
        eval_metric=eval_metric,
        eval_lower_is_better=eval_lower_is_better,
        model_name=model_name,
        pipeline_job_id=pipeline_job_id,
        test_data=test_dataset,
        evaluation_name=evaluation_name,
    )

    # Check that model lookup is performed, and the existing champion model is found
    mock_model_class.list.assert_called_once_with(
        filter=f'display_name="{model_name}"',
        location=location,
        project=project,
    )
    assert "is being challenged by new model" in caplog.text

    # Check champion wins in model comparison
    assert "Champion wins!" in caplog.text

    # Check model upload call
    mock_model_class.upload.assert_called_once_with(
        display_name=model_name,
        description=model_description,
        artifact_uri="dummy-model-uri",
        serving_container_image_uri=serving_container_image,
        parent_model=mock_champion_model.resource_name,
        is_default_version=False,
    )

    # Check model output URI
    assert vertex_model.uri == f"https://{location}-aiplatform.googleapis.com/v1/" + (
        str(mock_model_class.upload.return_value.versioned_resource_name)
    )

    # check evaluation import
    mock_model_service_client.return_value.import_model_evaluation.assert_called_once_with(  # noqa
        parent=mock_model_class.upload.return_value.versioned_resource_name,
        model_evaluation=mock.ANY,
    )
