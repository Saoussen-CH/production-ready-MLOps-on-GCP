import argparse
from google.cloud import aiplatform
from os import environ as env


def schedule_pipeline(
    template_path: str,
    pipeline_root: str,
    display_name: str,
    schedule_name: str,
    pipeline_type: str,
    cron: str,
    enable_caching: bool = False,
) -> aiplatform.pipeline_job_schedules.PipelineJobSchedule:
    """
    Schedule a Vertex AI pipeline run based on the provided configuration.

    Args:
        template_path (str): The path to the pipeline template in Artifact Registry.
        pipeline_root (str): The root path for pipeline artifacts (Cloud Storage URI).
        display_name (str): The display name for the pipeline.
        schedule_name (str): The name of the schedule.
        cron (str): Cron expression for scheduling the pipeline run.

    Returns:
        pipeline_job_schedules.PipelineJobSchedule: The scheduled pipeline job.
    """
    project = env.get("VERTEX_PROJECT_ID")
    location = env.get("VERTEX_LOCATION")
    bucket_uri = env.get("VERTEX_PIPELINE_ROOT")
    service_account = env.get("VERTEX_SA_EMAIL")
    bq_location = env.get("BQ_LOCATION")

    aiplatform.init(project=project, location=location)

    if pipeline_type == "training":
        parameters = {
            "project": project,
            "location": location,
            "training_job_display_name": f"{display_name}-training-job-on-{schedule_name}",  # noqa
            "base_output_dir": bucket_uri,
            "bq_location": bq_location,
        }

    else:
        parameters = {}

    pipeline_job = aiplatform.PipelineJob(
        template_path=template_path,
        pipeline_root=pipeline_root,
        display_name=display_name,
        parameter_values=parameters,
        enable_caching=enable_caching,
    )

    pipeline_job_schedule = pipeline_job.create_schedule(
        cron=cron,
        display_name=schedule_name,
        service_account=service_account,
    )
    pipeline_job_schedule.wait()
    print(f"Schedule created: {pipeline_job_schedule}")

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
        action="store_true",
        help="Enable caching for the pipeline run.",
    )

    args = parser.parse_args()

    schedule_pipeline(
        template_path=args.template_path,
        pipeline_root=args.pipeline_root,
        display_name=args.display_name,
        schedule_name=args.schedule_name,
        pipeline_type=args.pipeline_type,
        cron=args.cron,
        enable_caching=args.enable_caching,
    )


if __name__ == "__main__":
    main()
