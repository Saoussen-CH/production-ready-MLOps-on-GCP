import logging

from google.cloud import aiplatform
from pipelines.utils.trigger_pipeline import trigger_pipeline


def trigger_pipeline_from_payload(
    payload: dict, type: str, enable_caching: bool
) -> aiplatform.PipelineJob:
    """Triggers a pipeline run from a payload dict, JSON pipeline definition,
    and env variables.
    Args:
        payload (dict): payload containing attributes and data.
        template_path (str): File path (local or GCS) of compiled pipeline definition.
    """
    logging.info("Received payload: %s with job type: %s", payload, type)
    payload = convert_payload(payload)

    return trigger_pipeline(
        template_path=payload["attributes"]["template_path"],
        display_name="test_trigger_pipeline",
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
