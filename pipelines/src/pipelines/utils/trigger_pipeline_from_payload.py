import logging

from google.cloud import aiplatform
from pipelines.utils.trigger_pipeline import trigger_pipeline


def trigger_pipeline_from_payload(
    payload: dict, type: str, enable_caching: bool
) -> aiplatform.PipelineJob:
    """
    Trigger a Vertex Pipeline run from a payload dictionary.

    Args:
        payload (dict): The payload dictionary containing pipeline parameters.
        type (str): Type of the pipeline to trigger <training/prediction>.
        enable_caching (bool): Whether to enable caching for the pipeline.

    Returns:
        aiplatform.PipelineJob: the Vertex PipelineJob object
    """
    logging.info(f"Triggering pipeline with caching: {enable_caching}")

    # Extract parameters from the payload
    template_path = payload["attributes"]["template_path"]
    display_name = f"e2e-test-{type}-pipeline"
    timestamp = payload["data"].get("timestamp", "")
    use_latest_data = payload["data"].get("use_latest_data", True)

    return trigger_pipeline(
        template_path=template_path,
        display_name=display_name,
        type=type,
        enable_caching=enable_caching,
        timestamp=timestamp,
        use_latest_data=use_latest_data,
    )


def convert_payload(payload: dict) -> dict:
    """
    Processes the payload dictionary.
    Converts enable_caching and adds their defaults if they are missing.

    Args:
        payload (dict): Cloud Function event payload,
        or the contents of a payload JSON file

    Returns:
        dict: The processed payload dictionary
    """
    # Make a copy of the payload so we are not modifying the original
    payload = payload.copy()

    # If payload["data"] is missing, add it as an empty dict
    payload["data"] = payload.get("data", {})

    # Convert enable_caching to boolean if present
    if "enable_caching" in payload["data"]:
        payload["data"]["enable_caching"] = (
            payload["data"]["enable_caching"].lower() == "true"
        )

    # Add default values for timestamp and use_latest_data if they are missing
    payload["data"].setdefault("timestamp", "")
    payload["data"].setdefault("use_latest_data", True)

    return payload
