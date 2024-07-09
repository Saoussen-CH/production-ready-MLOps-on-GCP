if __name__ == "__main__":
    from google.cloud import aiplatform
    from os import environ as env

    project = env.get("VERTEX_PROJECT_ID")
    location = env.get("VERTEX_LOCATION")
    bucket_uri = env.get("BUCKET_URI")

    parameters = {
        "project": project,
        "location": location,
        "training_job_display_name": "taxifare-training-job",
        "base_output_dir": bucket_uri,
    }

    aiplatform.init(project=project, location=location)

    start_pipeline = aiplatform.pipeline_jobs.PipelineJob(
        display_name="taxifare-pipeline",
        template_path="taxifare-pipeline.yaml",
        parameter_values=parameters,
        pipeline_root=bucket_uri,
        enable_caching=True,
        location="us-central1",
    )

    start_pipeline.run()
