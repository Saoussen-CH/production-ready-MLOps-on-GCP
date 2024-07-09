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

    args = parser.parse_args()
    params = args.__dict__

    print(params)
    model.train_and_evaluate(params)
