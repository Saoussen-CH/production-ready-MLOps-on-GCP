import logging
from pipelines.training import pipeline as training_pipeline
from pipelines.prediction import pipeline as prediction_pipeline
from tests.e2e.test_e2e import pipeline_e2e_test

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_pipeline_run(
    pipeline_type: str, enable_caching: bool, timestamp: str, use_latest_data: bool
) -> None:
    """
    Tests if pipeline is run successfully.
    Triggers pipeline synchronously.
    Tests will fail if:
    - Any errors are thrown during execution.
    - Any of the expected component outputs are empty (size == 0kb).

    Arguments:
        pipeline_type (str): The type of pipeline to run ('training' or 'prediction').
        enable_caching (bool): Whether to enable caching for the pipeline.
        timestamp (str): Optional. Empty or a specific timestamp in ISO 8601 format.
        use_latest_data (bool): Whether to use the latest available data.

    Returns:
        None
    """

    if pipeline_type == "training":
        pipeline = training_pipeline
    elif pipeline_type == "prediction":
        pipeline = prediction_pipeline
    else:
        logger.error("Specify the pipeline type as 'training' or 'prediction'.")
        return

    logger.info(f"Running {pipeline} pipeline...")

    try:
        pipeline_e2e_test(
            pipeline,
            pipeline_type=pipeline_type,
            common_tasks={},
            enable_caching=enable_caching,
            timestamp=timestamp,
            use_latest_data=use_latest_data,
        )
        logger.info(f"{pipeline} pipeline ran successfully.")
    except Exception as e:
        logger.error(f"Error running {pipeline} pipeline: {e}")
        raise
