from kfp import compiler, dsl
from os import environ as env
import pathlib

from components import (
    lookup_model_op,
    model_batch_predict_op,
)

from google_cloud_pipeline_components.v1.bigquery import BigqueryQueryJobOp
from pipelines.utils.query import generate_query

# set training-serving skew thresholds and emails to receive alerts:
ALERT_EMAILS = []
NOTIFICATION_CHANNELS = []
SKEW_THRESHOLDS = {"defaultSkewThreshold": {"value": 0.001}}
# or set different thresholds per feature:
# SKEW_THRESHOLDS = {"skewThresholds": {"payment_type": {"value": 0.001}}, ... }


@dsl.pipeline(name="taxifare-batch-prediction-pipeline")
def pipeline(
    project: str = env.get("VERTEX_PROJECT_ID"),
    location: str = env.get("VERTEX_LOCATION"),
    bq_location: str = env.get("BQ_LOCATION"),
    bq_source_uri: str = "bigquery-public-data.chicago_taxi_trips.taxi_trips",
    dataset: str = "taxi_trips_dataset",
    timestamp: str = "2022-12-01 00:00:00",
    use_latest_data: bool = True,  # Parameter to use the latest data or fixed timestamp
    model_name: str = "taxi-traffic-model",
    machine_type: str = "n2-standard-4",
    min_replicas: int = 3,
    max_replicas: int = 10,
):
    """
    Prediction pipeline which:
     1. Looks up the default model version (champion).
     2. Runs a batch prediction job with BigQuery as input and output
     3. Optionally monitors training-serving skew

    Args:
        project (str): project id of the Google Cloud project
        location (str): location of the Google Cloud project
        bq_location (str): location of dataset in BigQuery
        bq_source_uri (str): `<project>.<dataset>.<table>` of ingestion data in BigQuery
        model_name (str): name of model
        dataset (str): dataset id to store staging data & predictions in BigQuery
        timestamp (str): Optional. Empty or a specific timestamp in ISO 8601 format
            (YYYY-MM-DDThh:mm:ss.sss±hh:mm or YYYY-MM-DDThh:mm:ss).
            If any time part is missing, it will be regarded as zero
        use_latest_data (bool): Whether to use the latest available data
        machine_type (str): Machine type to be used for Vertex Batch
            Prediction. Example machine_types - n1-standard-4, n1-standard-16 etc.
        min_replicas (int): Minimum no of machines to distribute the
            Vertex Batch Prediction job for horizontal scalability
        max_replicas (int): Maximum no of machines to distribute the
            Vertex Batch Prediction job for horizontal scalability
    """

    table = "prep_prediction_table"

    queries_folder = pathlib.Path(__file__).parent / "queries"

    prep_query = generate_query(
        input_file=queries_folder / "ingest_pred.sql",
        source=bq_source_uri,
        location=bq_location,
        dataset=f"{project}.{dataset}",
        table_=table,
        label="total_fare",  # Assuming the label is 'total_fare'
        start_timestamp=timestamp,
        use_latest_data=use_latest_data,
    )

    prep_op = BigqueryQueryJobOp(
        project=project,
        location="US",
        query=prep_query,
    ).set_display_name("Ingest & preprocess data")

    # lookup champion model
    champion_model = lookup_model_op(
        model_name=model_name,
        location=location,
        project=project,
        fail_on_model_not_found=True,
    ).set_display_name("Look up champion model")

    # batch predict from BigQuery to BigQuery
    (
        model_batch_predict_op(
            model=champion_model.outputs["model"],
            job_display_name="taxi-fare-predict-job",
            location=location,
            project=project,
            source_uri=f"bq://{project}.{dataset}.{table}",
            destination_uri=f"bq://{project}.{dataset}",
            source_format="bigquery",
            destination_format="bigquery",
            instance_config={
                "instanceType": "object",
            },
            machine_type=machine_type,
            starting_replica_count=min_replicas,
            max_replica_count=max_replicas,
            monitoring_training_dataset=champion_model.outputs["training_dataset"],
            monitoring_alert_email_addresses=ALERT_EMAILS,
            notification_channels=NOTIFICATION_CHANNELS,
            monitoring_skew_config=SKEW_THRESHOLDS,
        )
        .after(prep_op)
        .set_display_name("Run prediction job")
    )


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=pipeline, package_path="taxifare-prediction-pipeline.yaml"
    )
