import pytest
from google.cloud.aiplatform_v1.types import study
import components

get_hyperparameter_tuning_results_op = (
    components.get_hyperparameter_tuning_results_op.python_func
)


def test_get_hyperparameter_tuning_results_op_maximize(mocker):
    # Mock the external dependencies
    mock_aip = mocker.patch("google.cloud.aiplatform")
    mock_Parse = mocker.patch("google.protobuf.json_format.Parse")

    # Setup mock objects
    mock_job_resource = mocker.Mock()
    mock_job_resource.trials = [
        mocker.Mock(
            final_measurement=mocker.Mock(metrics=[mocker.Mock(value=1)]),
            parameters=[mocker.Mock(parameter_id="param1", value=1)],
        ),
        mocker.Mock(
            final_measurement=mocker.Mock(metrics=[mocker.Mock(value=2)]),
            parameters=[mocker.Mock(parameter_id="param1", value=2)],
        ),
    ]
    mock_gcp_resources_proto = mocker.Mock()
    mock_gcp_resources_proto.resources = [
        mocker.Mock(
            resource_uri="projects/project1/locations/location1/hyperparameterTuningJobs/job1"  # noqa: E501
        )
    ]

    # Mock the return values
    mock_Parse.return_value = mock_gcp_resources_proto
    mock_aip.HyperparameterTuningJob.get.return_value.gca_resource = mock_job_resource

    # Test input
    project = "project1"
    location = "location1"
    job_resource = '{"resources": [{"resource_uri": "projects/project1/locations/location1/hyperparameterTuningJobs/job1"}]}'  # noqa: E501
    study_spec_metrics = [{"goal": study.StudySpec.MetricSpec.GoalType.MAXIMIZE}]

    # Call the function
    result = get_hyperparameter_tuning_results_op(
        project, location, job_resource, study_spec_metrics
    )

    # Assert the result
    assert result == {"param1": 2}


def test_get_hyperparameter_tuning_results_op_minimize(mocker):
    # Mock the external dependencies
    mock_aip = mocker.patch("google.cloud.aiplatform")
    mock_Parse = mocker.patch("google.protobuf.json_format.Parse")

    # Setup mock objects
    mock_job_resource = mocker.Mock()
    mock_job_resource.trials = [
        mocker.Mock(
            final_measurement=mocker.Mock(metrics=[mocker.Mock(value=1)]),
            parameters=[mocker.Mock(parameter_id="param1", value=1)],
        ),
        mocker.Mock(
            final_measurement=mocker.Mock(metrics=[mocker.Mock(value=2)]),
            parameters=[mocker.Mock(parameter_id="param1", value=2)],
        ),
    ]
    mock_gcp_resources_proto = mocker.Mock()
    mock_gcp_resources_proto.resources = [
        mocker.Mock(
            resource_uri="projects/project1/locations/location1/hyperparameterTuningJobs/job1"  # noqa: E501
        )
    ]

    # Mock the return values
    mock_Parse.return_value = mock_gcp_resources_proto
    mock_aip.HyperparameterTuningJob.get.return_value.gca_resource = mock_job_resource

    # Test input
    project = "project1"
    location = "location1"
    job_resource = '{"resources": [{"resource_uri": "projects/project1/locations/location1/hyperparameterTuningJobs/job1"}]}'  # noqa: E501
    study_spec_metrics = [{"goal": study.StudySpec.MetricSpec.GoalType.MINIMIZE}]

    # Call the function
    result = get_hyperparameter_tuning_results_op(
        project, location, job_resource, study_spec_metrics
    )

    # Assert the result
    assert result == {"param1": 1}


def test_get_hyperparameter_tuning_results_op_multi_objective(mocker):
    # Mock the external dependencies
    mock_aip = mocker.patch("google.cloud.aiplatform")
    mock_Parse = mocker.patch("google.protobuf.json_format.Parse")

    # Setup mock objects
    mock_job_resource = mocker.Mock()
    mock_job_resource.trials = [
        mocker.Mock(
            final_measurement=mocker.Mock(metrics=[mocker.Mock(value=1)]),
            parameters=[mocker.Mock(parameter_id="param1", value=1)],
        ),
        mocker.Mock(
            final_measurement=mocker.Mock(metrics=[mocker.Mock(value=2)]),
            parameters=[mocker.Mock(parameter_id="param1", value=2)],
        ),
    ]
    mock_gcp_resources_proto = mocker.Mock()
    mock_gcp_resources_proto.resources = [
        mocker.Mock(
            resource_uri="projects/project1/locations/location1/hyperparameterTuningJobs/job1"  # noqa: E501
        )
    ]

    # Mock the return values
    mock_Parse.return_value = mock_gcp_resources_proto
    mock_aip.HyperparameterTuningJob.get.return_value.gca_resource = mock_job_resource

    # Test input
    project = "project1"
    location = "location1"
    job_resource = '{"resources": [{"resource_uri": "projects/project1/locations/location1/hyperparameterTuningJobs/job1"}]}'  # noqa: E501
    study_spec_metrics = [
        {"goal": study.StudySpec.MetricSpec.GoalType.MAXIMIZE},
        {"goal": study.StudySpec.MetricSpec.GoalType.MINIMIZE},
    ]

    # Call the function and assert the exception
    with pytest.raises(
        RuntimeError,
        match="Unable to determine best parameters for multi-objective hyperparameter tuning.",  # noqa: E501
    ):
        get_hyperparameter_tuning_results_op(
            project, location, job_resource, study_spec_metrics
        )
