import pathlib

from components import (
    extract_table_to_gcs_op,
    get_custom_job_results_op,
    get_training_args_dict_op,
    get_workerpool_spec_op,
    upload_best_model_op,
    get_hyperparameter_tuning_results_op,
)

from os import environ as env

from google_cloud_pipeline_components.v1.bigquery import BigqueryQueryJobOp
from google_cloud_pipeline_components.v1.custom_job import CustomTrainingJobOp
from google_cloud_pipeline_components.v1.hyperparameter_tuning_job import (
    HyperparameterTuningJobRunOp,
)
from google_cloud_pipeline_components.v1 import hyperparameter_tuning_job
from google.cloud.aiplatform import hyperparameter_tuning as hpt

from kfp import compiler, dsl

from pipelines.utils.query import generate_query


TRAINING_IMAGE = f"{VERTEX_LOCATION}-docker.pkg.dev/{VERTEX_PROJECT_ID}/mlops-docker-repo/{IMAGE_NAME}:{IMAGE_TAG}"  # noqa


bq_source_uri = "bigquery-public-data.chicago_taxi_trips.taxi_trips"
dataset = "prerocessing"
table = "taxi_fare"
label = "total_fare"
timestamp = "2022-12-01 00:00:00"


# define the metric spec for hyperparameter tuning
# for details:
# https://cloud.google.com/vertex-ai/docs/reference/rest/v1/StudySpec#MetricSpec
METRIC_SPEC = dict(val_root_mean_squared_error="minimize")

# define the parameter specs for tuning
# for details:
# https://cloud.google.com/vertex-ai/docs/reference/rest/v1/StudySpec#ParameterSpec
PARAMETER_SPEC = {
    "learning-rate": hpt.DoubleParameterSpec(min=0.0001, max=1, scale="log"),
    "batch-size": hpt.DiscreteParameterSpec(values=[128, 256, 512], scale="linear"),
}


PREDICTION_IMAGE = "us-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-11:latest"


@dsl.pipeline(name="taxifare-training-pipeline")
def pipeline(
    project: str = env.get("VERTEX_PROJECT_ID"),
    location: str = env.get("VERTEX_LOCATION"),
    bq_location: str = env.get("BQ_LOCATION"),
    bq_source_uri: str = "bigquery-public-data.chicago_taxi_trips.taxi_trips",
    dataset: str = "taxi_trips_dataset",
    timestamp: str = "2022-12-01 00:00:00",
    base_output_dir: str = "",
    training_job_display_name: str = "",
    model_name: str = "taxi-traffic-model",
    image_name: str = env.get("IMAGE_NAME"),
    image_tag: str = env.get("IMAGE_TAG"),
):
    """
    Training pipeline which:
     1. Preprocesses data in BigQuery
     2. Extracts data to Cloud Storage
     3. Trains a model using a custom prebuilt container
     4. Uploads the model to Model Registry
     5. Evaluates the model against a champion model
     6. Selects a new champion based on the primary metrics

    Args:
        project (str): project id of the Google Cloud project
        location (str): location of the Google Cloud project
        bq_location (str): location of dataset in BigQuery
        bq_source_uri (str): `<project>.<dataset>.<table>` of ingestion data in BigQuery
        model_name (str): name of model
        dataset (str): dataset id to store staging data & predictions in BigQuery
        timestamp (str): Optional. Empty or a specific timestamp in ISO 8601 format
            (YYYY-MM-DDThh:mm:ss.sss±hh:mm or YYYY-MM-DDThh:mm:ss).
            If any time part is missing, it will be regarded as zero.
        test_data_gcs_uri (str): Optional. GCS URI of static held-out test dataset.
    """
    PRIMARY_METRIC = "rootMeanSquaredError"
    queries_folder = pathlib.Path(__file__).parent / "queries"

    preprocessed_table = "preprocessed_data"

    TRAINING_IMAGE = f"{location}-docker.pkg.dev/{project}/mlops-docker-repo/{image_name}:{image_tag}"  # noqa

    # define the workerpool spec for the custom jobs
    # (https://cloud.google.com/vertex-ai/docs/reference/rest/v1/CustomJobSpec)
    WORKER_POOL_SPECS = [
        dict(
            machine_spec=dict(
                machine_type="n1-standard-4",
            ),
            replica_count=1,
            container_spec=dict(
                image_uri=TRAINING_IMAGE,
            ),
        )
    ]

    prep_query = generate_query(
        input_file=queries_folder / "ingest.sql",
        source=bq_source_uri,
        location=bq_location,
        dataset=f"{project}.{dataset}",
        table_=preprocessed_table,
        label=label,
        start_timestamp=timestamp,
    )

    prep_op = BigqueryQueryJobOp(
        project=project,
        location="US",
        query=prep_query,
    ).set_display_name("Ingest & preprocess data")

    split_train_query = generate_query(
        input_file=queries_folder / "repeatable_splitting.sql",
        source_dataset=f"{project}.{dataset}",
        source_table=preprocessed_table,
        num_lots=10,
        lots=tuple(range(8)),
    )

    split_valid_query = generate_query(
        input_file=queries_folder / "repeatable_splitting.sql",
        source_dataset=f"{project}.{dataset}",
        source_table=preprocessed_table,
        num_lots=10,
        lots="(8)",
    )

    split_test_query = generate_query(
        input_file=queries_folder / "repeatable_splitting.sql",
        source_dataset=f"{project}.{dataset}",
        source_table=preprocessed_table,
        num_lots=10,
        lots="(9)",
    )

    split_train_data = (
        BigqueryQueryJobOp(
            project=project,
            location=bq_location,
            query=split_train_query,
        )
        .after(prep_op)
        .set_display_name("Split train data")
    )

    train_dataset = (
        extract_table_to_gcs_op(bq_table=split_train_data.outputs["destination_table"])
        .after(split_train_data)
        .set_display_name("Extract training data from BigQuery to GCS")
    )

    split_valid_data = (
        BigqueryQueryJobOp(
            project=project,
            location=bq_location,
            query=split_valid_query,
        )
        .after(prep_op)
        .set_display_name("Split valid data")
    )

    valid_dataset = (
        extract_table_to_gcs_op(bq_table=split_valid_data.outputs["destination_table"])
        .after(split_valid_data)
        .set_display_name("Extract validation data from BigQuery to GCS")
    )

    split_test_data = (
        BigqueryQueryJobOp(
            project=project,
            location=bq_location,
            query=split_test_query,
        )
        .after(prep_op)
        .set_display_name("Split test data")
    )

    test_dataset = (
        extract_table_to_gcs_op(bq_table=split_test_data.outputs["destination_table"])
        .after(split_test_data)
        .set_display_name("Extract test data from BigQuery to GCS")
    )

    # define training args
    args = dict(
        train_data=train_dataset.outputs["dataset"],
        valid_data=valid_dataset.outputs["dataset"],
        test_data=test_dataset.outputs["dataset"],
        hypertune=True,
    )

    hypertune_args_step = get_training_args_dict_op(**args).set_display_name(
        "Get-Hypertune-Args"
    )

    # create the workerpool spec for hyperparameter tuning
    # dont provide hyperparams, because they are defined in the PARAMETER_SPEC
    # and directly passed to the hyperparameter tuning job
    hypertune_worker_pool_specs_step = get_workerpool_spec_op(
        worker_pool_specs=WORKER_POOL_SPECS,
        args=hypertune_args_step.output,
    ).set_display_name("Get-Hypertune-Worker-Pool-Spec")

    # create the actual hyperparameter tuning job
    # here you can choose how many trials to do and how many to run in parallel
    hypertune_step = HyperparameterTuningJobRunOp(
        display_name="hypertune-job",
        project=project,
        location=location,
        worker_pool_specs=hypertune_worker_pool_specs_step.output,
        study_spec_metrics=hyperparameter_tuning_job.utils.serialize_metrics(
            METRIC_SPEC
        ),
        study_spec_parameters=hyperparameter_tuning_job.utils.serialize_parameters(
            PARAMETER_SPEC
        ),
        max_trial_count=6,
        parallel_trial_count=2,
        base_output_directory=f"{base_output_dir}/hypertune-job",
    ).set_display_name("Hypertune-Job")

    # now we can extract the results of the hyperparameter tuning job
    hypertune_results_step = get_hyperparameter_tuning_results_op(
        project=project,
        location=location,
        job_resource=hypertune_step.output,
        study_spec_metrics=hyperparameter_tuning_job.utils.serialize_metrics(
            METRIC_SPEC
        ),
    ).set_display_name("Get-Hypertune-Results")

    # update our args dict for training
    args.update(dict(hypertune=False))

    # create the args dict
    training_args_step = get_training_args_dict_op(**args).set_display_name(
        "Get-Training-Args"
    )

    # create the workerpool spec for training
    training_worker_pool_specs_step = get_workerpool_spec_op(
        worker_pool_specs=WORKER_POOL_SPECS,
        hyperparams=hypertune_results_step.output,
        args=training_args_step.output,
    ).set_display_name("Get-Training-Worker-Pool-Spec")

    # Train the model
    custom_job_task = CustomTrainingJobOp(
        project=project,
        display_name=training_job_display_name,
        worker_pool_specs=training_worker_pool_specs_step.output,
        base_output_directory=f"{base_output_dir}/training-job",
        location=location,
    )

    # now we can extract the training results
    training_results_step = get_custom_job_results_op(
        project=project, location=location, job_resource=custom_job_task.output
    ).set_display_name("Get-Training-Results")

    upload_best_model_op(
        project=project,
        location=location,
        model=training_results_step.outputs["model"],
        model_eval_metrics=training_results_step.outputs["metrics"],
        test_data=test_dataset.outputs["dataset"],
        eval_metric=PRIMARY_METRIC,
        eval_lower_is_better=True,
        serving_container_image=PREDICTION_IMAGE,
        model_name=model_name,
        model_description="Predict price of a taxi trip.",
        pipeline_job_id="{{$.pipeline_job_name}}",
    ).set_display_name("Upload model")


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=pipeline, package_path="taxifare-training-pipeline.yaml"
    )
