from google.cloud import aiplatform
import argparse
from os import environ as env


def trigger_pipeline(
    template_path: str,
    display_name: str,
    type: str,
    enable_caching: bool = False,
) -> aiplatform.pipeline_jobs.PipelineJob:
    """Trigger a Vertex Pipeline run from a (local) compiled pipeline definition.

    Args:
        template_path (str): file path to the compiled YAML pipeline
        display_name (str): Display name to use for the PipelineJob
        type (str): Type of the pipeline to trigger <training/prediction>
        enable_caching (bool): Whether to enable caching for the pipeline

    Returns:
        aiplatform.pipeline_jobs.PipelineJob: the Vertex PipelineJob object
    """

    # Retrieve environment variables
    project = env.get("VERTEX_PROJECT_ID")
    location = env.get("VERTEX_LOCATION")
    bucket_uri = env.get("VERTEX_PIPELINE_ROOT")
    service_account = env.get("VERTEX_SA_EMAIL")

    # Set parameters based on pipeline type
    if type == "training":
        parameters = {
            "project": project,
            "location": location,
            "training_job_display_name": f"{display_name}-training-job",
            "base_output_dir": bucket_uri,
        }
    else:
        parameters = {}

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
        print(f"An error occurred: {e}")
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

    args = parser.parse_args()

    # Convert "true"/"false" to boolean
    enable_caching = args.enable_caching.lower() == "true"

    trigger_pipeline(
        template_path=args.template_path,
        display_name=args.display_name,
        type=args.type,
        enable_caching=enable_caching,
    )
