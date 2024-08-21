import logging

from google.cloud import aiplatform
from pipelines.utils.trigger_pipeline import trigger_pipeline


def trigger_pipeline_from_payload(
    payload: dict, type: str, enable_caching: bool
) -> aiplatform.PipelineJob:
    logging.info(f"Triggering pipeline with caching: {enable_caching}")
    template_path = payload["attributes"]["template_path"]
    display_name = f"e2e-test-{type}-pipeline"

    return trigger_pipeline(
        template_path=template_path,
        display_name=display_name,
        type=type,
        enable_caching=enable_caching,
    )


def convert_payload(payload: dict) -> dict:
    """
    Processes the payload dictionary.
    Converts enable_caching and adds their defaults if they are missing.

    Args:
        payload (dict): Cloud Function event payload,
        or the contents of a payload JSON file
    """

    # make a copy of the payload so we are not modifying the original
    payload = payload.copy()

    # if payload["data"] is missing, add it as empty dict
    payload["data"] = payload.get("data", {})

    return payload
