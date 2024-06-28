from kfp.dsl import component, Metrics, Output, Model


@component(
    base_image="python:3.10.14",
    packages_to_install=[
        "google-cloud-pipeline-components==2.14.1",
        "google-cloud-aiplatform==1.55.0",
    ],
)
def get_custom_job_results_op(
    project: str,
    location: str,
    job_resource: str,
    model: Output[Model],
    metrics: Output[Metrics],
):
    import json
    import shutil
    from pathlib import Path
    import google.cloud.aiplatform as aip
    from google.protobuf.json_format import Parse
    from google_cloud_pipeline_components.proto.gcp_resources_pb2 import GcpResources

    aip.init(project=project, location=location)

    training_gcp_resources = Parse(job_resource, GcpResources())
    custom_job_id = training_gcp_resources.resources[0].resource_uri
    custom_job_name = custom_job_id[custom_job_id.find("project"):]

    job_resource = aip.CustomJob.get(custom_job_name).gca_resource

    job_base_dir = job_resource.job_spec.base_output_directory.output_uri_prefix

    
    job_base_dir_fuse = job_base_dir.replace("gs://", "/gcs/")
    model_uri_fuse = model.uri.replace("gs://", "/gcs/")


    shutil.copytree(f"{job_base_dir_fuse}/model", Path(model_uri_fuse), dirs_exist_ok=True)
    
    

    with open(f"{job_base_dir_fuse}/metrics/metrics.json") as fh:
        metrics_dict = json.load(fh)

    for k, v in metrics_dict.items():
        metrics.log_metric(k, v)
    
    with open(metrics.path, "w") as fh:
        json.dump(metrics_dict, fh)
        
    shutil.rmtree(f"{job_base_dir_fuse}/model")
    shutil.rmtree(f"{job_base_dir_fuse}/metrics")
 