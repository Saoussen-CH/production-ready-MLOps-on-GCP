import json
import os
import logging
import functions_framework
import requests
import google.auth
import google.auth.transport.requests
from google.cloud import pubsub_v1

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
    project_id = config["project"]
    location = config["location"]
    pipeline_root = config["base_output_dir"]

    parameters = {
        "project": project_id,
        "location": location,
        "bq_location": config["bq_location"],
        "use_latest_data": config["use_latest_data"],
        "timestamp": config["timestamp"],
        "base_output_dir": pipeline_root,
    }

    if config["type"] == "training":
        template_uri = config["training_template_path"]
        parameters.update(
            {"training_job_display_name": f"{config['display_name']}-training-job"}
        )
        submit_pipeline_request(template_uri, config, parameters)

        subscribe_to_pubsub(config)

    elif config["type"] == "prediction":
        template_uri = config["prediction_template_path"]
        parameters.update(
            {"prediction_job_display_name": f"{config['display_name']}-prediction-job"}
        )
        submit_pipeline_request(template_uri, config, parameters)


def submit_pipeline_request(template_uri, config, parameters):
    request_body = {
        "name": f"{config['display_name']}-pipeline",
        "displayName": f"{config['display_name']}-pipeline",
        "runtimeConfig": {
            "gcsOutputDirectory": config["base_output_dir"],
            "parameterValues": parameters,
        },
        "templateUri": template_uri,
    }

    pipeline_url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{config['project']}/locations/{config['location']}/pipelineJobs"  # noqa
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
    subscription_path = subscriber.subscription_path(config["project"], topic_name)

    def callback(message):
        message.ack()
        print(f"Received message: {message.data}")
        trigger_prediction_pipeline_after_training(config)

    subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}...")


def trigger_prediction_pipeline_after_training(config):
    config["type"] = "prediction"
    submit_pipeline_job(json.dumps(config))
