if __name__ == "__main__":
    from google.cloud import aiplatform

    REGION='us-central1'
    BUCKET='mlops_pipeline_t'
    BUCKET_URI=f"gs://{BUCKET}"
    MODEL_DIR=f"gs://{BUCKET}/model"
    PROJECT_ID="mlops-learning-422012"
    project = 'mlops-learning-422012'
    location= "us-central1"

    parameters = {
        "project": PROJECT_ID,
        "location": REGION,
        "training_job_display_name": "taxifare-training-job",
        "base_output_dir": BUCKET_URI,
        #"model_dir": MODEL_DIR,
    }

    aiplatform.init(project=project, location=location)

    start_pipeline = aiplatform.pipeline_jobs.PipelineJob(
        display_name="taxifare-pipeline",
        template_path="taxifare-pipeline.yaml",
        parameter_values=parameters,
        pipeline_root=BUCKET_URI,
        enable_caching=False,
        location="us-central1",
    )

    start_pipeline.run()