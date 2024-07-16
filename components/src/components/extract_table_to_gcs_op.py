from kfp.dsl import Dataset, Artifact, component, Input, Output


@component(
    base_image="python:3.10.14", packages_to_install=["google-cloud-bigquery==3.24.0"]
)
def extract_table_to_gcs_op(
    bq_table: Input[Artifact],
    dataset: Output[Dataset],
    location: str = "US",
) -> None:
    """
    Extract a Big Query table into Google Cloud Storage.
    """

    import google.cloud.bigquery as bq

    project_id = bq_table.metadata["projectId"]
    dataset_id = bq_table.metadata["datasetId"]
    table_id = bq_table.metadata["tableId"]

    # Get the table generated on the previous component
    full_table_id = f"{project_id}.{dataset_id}.{table_id}"
    table = bq.table.Table(table_ref=full_table_id)

    # Initiate the Big Query client to connect with the project
    # job_config = bq.job.ExtractJobConfig(**{})
    client = bq.client.Client(project=project_id, location=location)

    # Submit the extract table job to store on GCS
    extract_job = client.extract_table(table, dataset.uri)

    # Wait for the extract job to complete
    extract_job.result()
