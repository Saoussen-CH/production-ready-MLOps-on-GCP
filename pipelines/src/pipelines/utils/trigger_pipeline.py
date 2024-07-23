from google.cloud import aiplatform
from os import environ as env
import argparse


def trigger_pipeline(
    template_path: str,
    display_name: str,
    type: str,
) -> aiplatform.pipeline_jobs.PipelineJob:
    """Trigger a Vertex Pipeline run from a (local) compiled pipeline definition.

    Args:
        template_path (str): file path to the compiled YAML pipeline
        display_name (str): Display name to use for the PipelineJob

    Returns:
        aiplatform.pipeline_jobs.PipelineJob: the Vertex PipeliclearneJob object
    """

    project = env.get("VERTEX_PROJECT_ID")
    location = env.get("VERTEX_LOCATION")
    bucket_uri = env.get("VERTEX_PIPELINE_ROOT")

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
        enable_caching=True,
        location=location,
    )

    start_pipeline.run()

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
        help="Type of the pipeline to tirgger <training/prediction>",
        type=str,
    )

    args = parser.parse_args()

    trigger_pipeline(
        template_path=args.template_path,
        display_name=args.display_name,
        type=args.type,
    )
