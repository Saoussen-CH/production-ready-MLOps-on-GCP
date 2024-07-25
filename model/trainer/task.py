"""Argument definitions for model training code in `trainer.model`."""

import argparse

from trainer import model
import os
import json


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--train-data", type=str, required=True)

    parser.add_argument("--valid-data", type=str, required=True)

    parser.add_argument("--test-data", type=str, required=True)

    parser.add_argument(
        "--model", default=os.getenv("AIP_MODEL_DIR"), type=str, help=""
    )

    parser.add_argument(
        "--checkpoints", default=os.getenv("AIP_CHECKPOINT_DIR"), type=str, help=""
    )

    parser.add_argument("--metrics", type=str, default="")
    # required=True)

    parser.add_argument("--hparams", default={}, type=json.loads)

    parser.add_argument("--hypertune", type=bool, default=False)

    # tunable parameters
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=0.001)

    args = parser.parse_args()
    params = args.__dict__

    model.train_and_evaluate(params)
