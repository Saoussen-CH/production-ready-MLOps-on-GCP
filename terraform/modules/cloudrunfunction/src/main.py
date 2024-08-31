import json
import os
import re
import logging
import functions_framework
import requests
import google.auth
import google.auth.transport.requests
from google.cloud import pubsub_v1
from kfp.registry import RegistryClient


logging.basicConfig(level=logging.INFO)


@functions_framework.cloud_event
def mlops_entrypoint(event):
    logging.info(f"Environment variables: {os.environ}")

    pipeline_config = os.getenv("PIPELINE_CONFIG")
    if pipeline_config is None:
        logging.error("PIPELINE_CONFIG environment variable is not set")
        raise ValueError("PIPELINE_CONFIG environment variable is not set")

    logging.info(f"PIPELINE_CONFIG: {pipeline_config}")

    try:
        pipeline_config_dict = json.loads(pipeline_config)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse PIPELINE_CONFIG: {e}")
        raise ValueError("PIPELINE_CONFIG is not a valid JSON string")

    logging.info(f"Parsed PIPELINE_CONFIG: {pipeline_config_dict}")

    submit_pipeline_job(pipeline_config_dict)


def submit_pipeline_job(config):
    project_id = os.getenv("VERTEX_PROJECT_ID")
    location = os.getenv("VERTEX_LOCATION")
    pipeline_root = os.getenv("VERTEX_PIPELINE_ROOT")
    service_account = os.getenv("VERTEX_SA_EMAIL")

    parameters = {
        "project": project_id,
        "location": location,
        "bq_location": config["bq_location"],
        "use_latest_data": config["use_latest_data"],
        "timestamp": config["timestamp"],
        "base_output_dir": pipeline_root,
    }

    if config["type"] == "training":
        template_uri = get_package_digest_uri(config["training_template_path"])
        logging.info(f"training_template_uri: {template_uri}")
        parameters.update(
            {"training_job_display_name": f"{config['display_name']}-training-job"}
        )
        submit_pipeline_request(
            template_uri,
            config,
            parameters,
            service_account,
            pipeline_root,
            project_id,
            location,
        )

        subscribe_to_pubsub(config)

    elif config["type"] == "prediction":
        template_uri = get_package_digest_uri(config["prediction_template_path"])
        logging.info(f"prediction_template_uri: {template_uri}")
        parameters.update(
            {"prediction_job_display_name": f"{config['display_name']}-prediction-job"}
        )
        submit_pipeline_request(
            template_uri,
            config,
            parameters,
            service_account,
            pipeline_root,
            project_id,
            location,
        )


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


def submit_pipeline_request(
    template_uri,
    config,
    parameters,
    service_account,
    pipeline_root,
    project_id,
    location,
):
    request_body = {
        "name": f"{config['display_name']}-pipeline",
        "displayName": f"{config['display_name']}-pipeline",
        "runtimeConfig": {
            "gcsOutputDirectory": pipeline_root,
            "parameterValues": parameters,
        },
        "templateUri": template_uri,
        "serviceAccount": service_account,
    }

    pipeline_url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/pipelineJobs"  # noqa
    creds, project = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    response = requests.request(
        "POST", pipeline_url, headers=headers, data=json.dumps(request_body)
    )
    print(response.text)


def subscribe_to_pubsub(config):
    subscriber = pubsub_v1.SubscriberClient()
    topic_name = config["pubsub_topic_name"]
    subscription_path = subscriber.subscription_path(
        os.getenv("VERTEX_PROJECT_ID"), topic_name
    )

    def callback(message):
        message.ack()
        print(f"Received message: {message.data}")
        trigger_prediction_pipeline_after_training(config)

    subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}...")


def trigger_prediction_pipeline_after_training(config):
    config["type"] = "prediction"
    submit_pipeline_job(json.dumps(config))
