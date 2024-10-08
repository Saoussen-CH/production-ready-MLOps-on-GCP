import argparse
from google.cloud import aiplatform
from os import environ as env
import logging
import re
from kfp.registry import RegistryClient


def get_package_digest_uri(version_uri):
    # Check if the URI already contains a digest
    if "sha256:" in version_uri:
        return version_uri

    # Parse the version URI to extract the necessary components
    match = re.match(
        r"https://([\w\-]+)-kfp\.pkg\.dev/([\w\-]+)/([\w\-]+)/([\w\-]+)/([\w\-.]+)",
        version_uri,
    )
    if not match:
        raise ValueError(f"Invalid version URI: {version_uri}")

    region, project, repo, package_name, tag = match.groups()
    logging.info(
        f"Parsed URI components: region={region}, project={project}, repo={repo}, package={package_name}, tag={tag}"  # noqa
    )

    # Initialize the RegistryClient
    host = f"https://{region}-kfp.pkg.dev/{project}/{repo}"
    client = RegistryClient(host=host)

    # Get the tag metadata
    try:
        metadata = client.get_tag(package_name, tag)
    except Exception as e:
        logging.error(f"Failed to get tag metadata: {e}")
        raise

    # Extract the version (digest) from the metadata
    version = metadata["version"]
    logging.info(f"version= {version}")
    if "sha256:" not in version:
        raise ValueError(f"Invalid version format: {version}")

    version = version[version.find("sha256:") :]
    logging.info(f"version sha256 = {version}")

    # Construct the digest URI
    digest_uri = (
        f"https://{region}-kfp.pkg.dev/{project}/{repo}/{package_name}/{version}"
    )
    logging.info(f"digest_uri: {digest_uri}")

    return digest_uri


def schedule_pipeline(
    template_path: str,
    pipeline_root: str,
    display_name: str,
    schedule_name: str,
    pipeline_type: str,
    cron: str,
    enable_caching: bool = False,
    use_latest_data: bool = True,
    timestamp: str = "",
) -> aiplatform.pipeline_job_schedules.PipelineJobSchedule:
    """
    Schedule a Vertex AI pipeline run based on the provided configuration.

    Args:
        template_path (str): The path to the pipeline template in Artifact Registry.
        pipeline_root (str): The root path for pipeline artifacts (Cloud Storage URI).
        display_name (str): The display name for the pipeline.
        schedule_name (str): The name of the schedule.
        pipeline_type (str): The type of pipeline (training or prediction).
        cron (str): Cron expression for scheduling the pipeline run.
        enable_caching (bool): Whether to enable caching for the pipeline run.
        use_latest_data (bool): Whether to use the latest data or a fixed timestamp.
        timestamp (str): The timestamp for the pipeline in ISO 8601 format.

    Returns:
        pipeline_job_schedules.PipelineJobSchedule: The scheduled pipeline job.
    """

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
        "use_latest_data": use_latest_data,
        "timestamp": timestamp,
    }

    if pipeline_type == "training":
        parameters.update(
            {
                "training_job_display_name": f"{display_name}-training-job",
                "base_output_dir": bucket_uri,
            }
        )
    elif pipeline_type == "prediction":
        pass  # No additional parameters for prediction
    else:
        raise ValueError(f"Unsupported pipeline type: {pipeline_type}")

    template_uri = get_package_digest_uri(template_path)
      # Initialize AI Platform
    aiplatform.init(project=project, location=location)
    
    pipeline_job = aiplatform.PipelineJob(
        template_path=template_uri,
        pipeline_root=pipeline_root,
        display_name=display_name,
        parameter_values=parameters,
        enable_caching=enable_caching,
    )

    pipeline_job_schedule = aiplatform.PipelineJobSchedule(
        pipeline_job=pipeline_job,
        display_name=schedule_name,
    )

    pipeline_job_schedule.create(
        cron=cron,
        service_account=service_account,
    )

    logging.info(f"Schedule created: {pipeline_job_schedule}")

    return pipeline_job_schedule


def main():
    parser = argparse.ArgumentParser(
        description="Schedule a pipeline based on the pipeline type."
    )
    parser.add_argument(
        "--pipeline_type",
        required=True,
        choices=["training", "prediction"],
        help="Type of pipeline to schedule.",
    )
    parser.add_argument(
        "--template_path",
        required=True,
        help="Path to the pipeline template in Cloud Artifact Registry.",
    )
    parser.add_argument(
        "--pipeline_root",
        required=True,
        help="Root path for the pipeline.",
    )
    parser.add_argument(
        "--display_name",
        required=True,
        help="Display name for the pipeline.",
    )
    parser.add_argument(
        "--schedule_name",
        required=True,
        help="Name for the schedule.",
    )

    parser.add_argument(
        "--cron",
        required=True,
        help="Cron expression for scheduling.",
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

    # Log the arguments for debugging
    logging.info(f"enable_caching: {enable_caching}")
    logging.info(f"use_latest_data: {use_latest_data}")
    
    schedule_pipeline(
        template_path=args.template_path,
        pipeline_root=args.pipeline_root,
        display_name=args.display_name,
        schedule_name=args.schedule_name,
        pipeline_type=args.pipeline_type,
        cron=args.cron,
        enable_caching=enable_caching,
        use_latest_data=use_latest_data,
        timestamp=args.timestamp,
    )


if __name__ == "__main__":
    main()
