from kfp.registry import RegistryClient
from os import environ as env
from typing import List
import argparse


def upload_pipeline(file_name: str, tags: List[str]) -> tuple[str, str]:
    """Upload a compiled YAML pipeline to Artifact Registry

    Args:
       file_name (str): File path to the compiled YAML pipeline
       tags (List[str]): List of tags to use for the uploaded pipeline

    Returns:
       A tuple of the package name and the version.
    """

    host = env.get("KFP_TEMPLATE_AR")

    client = RegistryClient(host=host)

    return client.upload_pipeline(
        file_name=file_name,
        tags=tags,  # ["v1", "latest"],
        extra_headers={
            "description": "This is Kubeflow pipeline template for taxifare."
        },
    )

    # TEMPLATE_URI = f"{host}/{TEMPLATE_NAME}/latest"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--template_path", type=str, required=True)
    parser.add_argument("--tag", type=str, action="append")
    parsed_args = parser.parse_args()

    upload_pipeline(
        file_name=parsed_args.template_path,
        tags=parsed_args.tag,
    )
