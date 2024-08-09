from kfp.dsl import component


@component(
    base_image="python:3.10.14",
    packages_to_install=[
        "google-cloud-pipeline-components==2.14.1",
        "google-cloud-aiplatform==1.55.0",
    ],
)
def get_hyperparameter_tuning_results_op(
    project: str, location: str, job_resource: str, study_spec_metrics: list
) -> dict:
    import google.cloud.aiplatform as aip
    from google_cloud_pipeline_components.proto.gcp_resources_pb2 import GcpResources
    from google.protobuf.json_format import Parse
    from google.cloud.aiplatform_v1.types import study

    aip.init(project=project, location=location)

    gcp_resources_proto = Parse(job_resource, GcpResources())
    tuning_job_id = gcp_resources_proto.resources[0].resource_uri
    tuning_job_name = tuning_job_id[tuning_job_id.find("project") :]

    job_resource = aip.HyperparameterTuningJob.get(tuning_job_name).gca_resource

    trials = job_resource.trials

    if len(study_spec_metrics) > 1:
        raise RuntimeError(
            "Unable to determine best parameters for multi-objective hyperparameter tuning."  # noqa: E501
        )

    goal = study_spec_metrics[0]["goal"]
    if goal == study.StudySpec.MetricSpec.GoalType.MAXIMIZE:
        best_fn = max
    elif goal == study.StudySpec.MetricSpec.GoalType.MINIMIZE:
        best_fn = min
    best_trial = best_fn(
        trials, key=lambda trial: trial.final_measurement.metrics[0].value
    )

    return {p.parameter_id: p.value for p in best_trial.parameters}
