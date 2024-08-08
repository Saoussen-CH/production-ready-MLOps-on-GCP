from google.cloud import aiplatform
from os import environ as env
import argparse


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

    project = env.get("VERTEX_PROJECT_ID")
    location = env.get("VERTEX_LOCATION")
    bucket_uri = env.get("VERTEX_PIPELINE_ROOT")
    service_account = env.get("VERTEX_SA_EMAIL")

    if type == "training":
        parameters = {
            "project": project,
            "location": location,
            "training_job_display_name": f"{display_name}-training-job",
            "base_output_dir": bucket_uri,
        }

    else:
        parameters = {}

    aiplatform.init(project=project, location=location)

    start_pipeline = aiplatform.pipeline_jobs.PipelineJob(
        display_name=display_name,
        template_path=template_path,
        parameter_values=parameters,
        pipeline_root=bucket_uri,
        enable_caching=enable_caching,
        location=location,
    )

    start_pipeline.run(service_account=service_account)

    start_pipeline.wait()

    return start_pipeline


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--template_path",
        help="Path to the compiled pipeline (YAML)",
        type=str,
    )
    parser.add_argument(
        "--display_name",
        help="Display name for the PipelineJob",
        type=str,
    )

    parser.add_argument(
        "--type",
        help="Type of the pipeline to trigger <training/prediction>",
        type=str,
    )

    parser.add_argument(
        "--enable_caching",
        help="Whether to enable caching for the pipeline",
        type=bool,
        default=False,
    )

    args = parser.parse_args()

    trigger_pipeline(
        template_path=args.template_path,
        display_name=args.display_name,
        type=args.type,
        enable_caching=args.enable_caching,
    )
