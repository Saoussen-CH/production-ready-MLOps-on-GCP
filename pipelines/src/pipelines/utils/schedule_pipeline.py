import argparse
from google.cloud import aiplatform


def schedule_pipeline(
    template_path: str,
    pipeline_root: str,
    display_name: str,
    schedule_name: str,
    cron: str,
    max_concurrent_run_count: int,
    max_run_count: int,
    enable_caching: bool = False,
) -> aiplatform.pipeline_jobs.PipelineJobSchedule:
    """
    Schedule a Vertex AI pipeline run based on the provided configuration.

    Args:
        template_path (str): The path to the pipeline template in Artifact Registry.
        pipeline_root (str): The root path for pipeline artifacts (Cloud Storage URI).
        display_name (str): The display name for the pipeline.
        schedule_name (str): The name of the schedule.
        cron (str): Cron expression for scheduling the pipeline run.
        max_concurrent_run_count (int): Maximum number of concurrent runs.

    Returns:
        aiplatform.pipeline_jobs.PipelineJobSchedule: The scheduled pipeline job.
    """

    pipeline_job = aiplatform.PipelineJob(
        template_path=template_path,
        pipeline_root=pipeline_root,
        display_name=display_name,
        enable_caching=enable_caching,
    )

    pipeline_job_schedule = pipeline_job.create_schedule(
        cron=cron,
        display_name=schedule_name,
    )

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
        "--max_concurrent_run_count",
        type=int,
        required=True,
        help="Maximum number of concurrent runs.",
    )
    parser.add_argument(
        "--max_run_count",
        type=int,
        required=True,
        help="Maximum number of runs.",
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
        cron=args.cron,
        enable_caching=args.enable_caching,
    )


if __name__ == "__main__":
    main()
