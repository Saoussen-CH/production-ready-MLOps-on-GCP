from google.cloud import aiplatform
import argparse
from os import environ as env

import logging


def trigger_pipeline(
    template_path: str,
    display_name: str,
    type: str,
    enable_caching: bool = False,
    timestamp: str = "2022-12-01 00:00:00",
    use_latest_data: bool = True,
) -> aiplatform.pipeline_jobs.PipelineJob:
    """Trigger a Vertex Pipeline run from a (local) compiled pipeline definition.

    Args:
        template_path (str): file path to the compiled YAML pipeline
        display_name (str): Display name to use for the PipelineJob
        type (str): Type of the pipeline to trigger <training/prediction>
        enable_caching (bool): Whether to enable caching for the pipeline
        timestamp (str): Optional. Empty or a specific timestamp in ISO 8601 format
            (YYYY-MM-DDThh:mm:ss.sss±hh:mm or YYYY-MM-DDThh:mm:ss).
            If any time part is missing, it will be regarded as zero
        use_latest_data (bool): Whether to use the latest available data
    Returns:
        aiplatform.pipeline_jobs.PipelineJob: the Vertex PipelineJob object
    """

    logging.info(f"Enable Caching in Trigger: {enable_caching}")
    logging.info(f"Enable use_latest_data: {use_latest_data}")
    logging.info(f"Enable use_latest_data: {timestamp}")

    # Retrieve environment variables
    project = env.get("VERTEX_PROJECT_ID")
    location = env.get("VERTEX_LOCATION")
    bucket_uri = env.get("VERTEX_PIPELINE_ROOT")
    service_account = env.get("VERTEX_SA_EMAIL")
    bq_location = env.get("BQ_LOCATION")

    # Validate environment variables
    if not all([project, location, bucket_uri, service_account, bq_location]):
        raise ValueError("One or more required environment variables are missing.")

    # Set parameters based on pipeline type
    parameters = {
        "project": project,
        "location": location,
        "bq_location": bq_location,
        "timestamp": timestamp,
        "use_latest_data": use_latest_data,
    }

    if type == "training":
        parameters.update(
            {
                "training_job_display_name": f"{display_name}-training-job",
                "base_output_dir": bucket_uri,
            }
        )
    elif type == "prediction":
        pass  # No additional parameters for prediction
    else:
        raise ValueError(f"Unsupported pipeline type: {type}")

    # Initialize AI Platform
    aiplatform.init(project=project, location=location)

    # Create and run the pipeline job
    start_pipeline = aiplatform.pipeline_jobs.PipelineJob(
        display_name=display_name,
        template_path=template_path,
        parameter_values=parameters,
        pipeline_root=bucket_uri,
        enable_caching=enable_caching,
        location=location,
    )

    try:
        start_pipeline.run(service_account=service_account)
        start_pipeline.wait()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise

    return start_pipeline


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--template_path",
        help="Path to the compiled pipeline (YAML)",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--display_name",
        help="Display name for the PipelineJob",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--type",
        help="Type of the pipeline to trigger <training/prediction>",
        type=str,
        choices=["training", "prediction"],
        required=True,
    )
    parser.add_argument(
        "--enable_caching",
        help="Whether to enable caching for the pipeline",
        type=str,
        choices=["true", "false"],
        default="false",
    )
    parser.add_argument(
        "--timestamp",
        help="Optional. Empty or a specific timestamp in ISO 8601 format",
        type=str,
        default="",
    )
    parser.add_argument(
        "--use_latest_data",
        help="Whether to use the latest available data or the fixed timestamp",
        type=str,
        choices=["true", "false"],
        default="true",
    )

    args = parser.parse_args()

    # Convert "true"/"false" to boolean
    enable_caching = args.enable_caching.lower() == "true"
    use_latest_data = args.use_latest_data.lower() == "true"

    trigger_pipeline(
        template_path=args.template_path,
        display_name=args.display_name,
        type=args.type,
        enable_caching=enable_caching,
        timestamp=args.timestamp,
        use_latest_data=use_latest_data,
    )
