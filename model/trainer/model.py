"""Data prep, train and evaluate DNN model."""

import os
import json
import logging
import sys

import tensorflow as tf
from pathlib import Path
from tensorflow.data import Dataset
from tensorflow.keras import Input, Model, optimizers
from tensorflow.keras.layers import Dense, Normalization, StringLookup, Concatenate

# numeric/categorical features in Chicago trips dataset to be preprocessed
import hypertune


class HyperTuneCallback(tf.keras.callbacks.Callback):
    def __init__(self, metric=None) -> None:
        super().__init__()
        self.metric = metric
        self.hpt = hypertune.HyperTune()

    def on_epoch_end(self, epoch, logs=None):
        if logs and self.metric in logs:
            self.hpt.report_hyperparameter_tuning_metric(
                hyperparameter_metric_tag=self.metric,
                metric_value=logs[self.metric],
                global_step=epoch,
            )


# used for monitoring during prediction time
TRAINING_DATASET_INFO = "training_dataset.json"

DEFAULT_HPARAMS = dict(
    batch_size=100,
    epochs=10,
    loss_fn="MeanSquaredError",
    optimizer="Adam",
    learning_rate=0.001,
    hidden_units=[(10, "relu")],
    early_stopping_epochs=5,
    label="total_fare",
    distribute_strategy="single",
)

logging.getLogger().setLevel(logging.INFO)


def create_dataset(input_data: str, label_name: str, model_params: dict) -> Dataset:
    logging.info(f"Creating dataset from CSV file(s) at {input_data}...")
    created_dataset = tf.data.experimental.make_csv_dataset(
        file_pattern=str(input_data),
        batch_size=model_params["batch_size"],
        label_name=label_name,
        num_epochs=model_params["epochs"],
        shuffle=True,
        shuffle_buffer_size=1000,
        num_rows_for_inference=20000,
    )
    return created_dataset


def normalization(name: str, dataset: Dataset) -> Normalization:
    logging.info(f"Normalizing numerical input '{name}'...")
    normalizer = Normalization(axis=None, name=f"normalize_{name}")
    normalizer.adapt(dataset.map(lambda x, _: x[name]))
    return normalizer


def str_lookup(name: str, dataset: Dataset, output_mode: str) -> StringLookup:
    logging.info(f"Encoding categorical input '{name}' ({output_mode})...")
    index = StringLookup(
        output_mode=output_mode, name=f"str_lookup_{output_mode}_{name}"
    )
    index.adapt(dataset.map(lambda x, _: x[name]))
    logging.info(f"Vocabulary: {index.get_vocabulary()}")
    return index


def transform(dataset):
    # create inputs (scalars with shape `()`)
    NUM_COLS = ["dayofweek", "hourofday", "trip_distance", "trip_miles", "trip_seconds"]

    ORD_COLS = ["company"]

    OHE_COLS = ["payment_type"]

    num_ins = {name: Input(shape=(), name=name, dtype=tf.float32) for name in NUM_COLS}
    ord_ins = {name: Input(shape=(), name=name, dtype=tf.string) for name in ORD_COLS}
    cat_ins = {name: Input(shape=(), name=name, dtype=tf.string) for name in OHE_COLS}

    all_ins = {**num_ins, **ord_ins, **cat_ins}
    exp_ins = {n: tf.expand_dims(i, axis=-1) for n, i in all_ins.items()}

    # preprocess expanded inputs
    num_encoded = [normalization(n, dataset)(exp_ins[n]) for n in NUM_COLS]
    ord_encoded = [str_lookup(n, dataset, "int")(exp_ins[n]) for n in ORD_COLS]
    ohe_encoded = [str_lookup(n, dataset, "one_hot")(exp_ins[n]) for n in OHE_COLS]

    # ensure ordinal encoded layers is of type float32 (like the other layers)
    ord_encoded = [tf.cast(x, tf.float32) for x in ord_encoded]

    # concat encoded inputs and add dense layers including output layer
    x = num_encoded + ord_encoded + ohe_encoded

    return x, all_ins


def build_and_compile_model(dataset: Dataset, model_params: dict) -> Model:
    x, all_ins = transform(dataset)
    x = Concatenate()(x)
    for units, activation in model_params["hidden_units"]:
        x = Dense(units, activation=activation)(x)
    x = Dense(1, name="output", activation="linear")(x)

    model = Model(inputs=all_ins, outputs=x, name="nn_model")
    model.summary()

    logging.info(f"Use optimizer {model_params['optimizer']}")
    optimizer = optimizers.get(model_params["optimizer"])
    optimizer.learning_rate = model_params["learning_rate"]

    # Create metrics within the distribution strategy scope
    with tf.distribute.get_strategy().scope():
        metrics = [
            tf.keras.metrics.RootMeanSquaredError(name="root_mean_squared_error"),
            tf.keras.metrics.MeanAbsoluteError(name="mean_absolute_error"),
            tf.keras.metrics.MeanAbsolutePercentageError(
                name="mean_absolute_percentage_error"
            ),
            tf.keras.metrics.MeanSquaredLogarithmicError(
                name="mean_squared_logarithmic_error"
            ),
        ]

    model.compile(
        loss=model_params["loss_fn"],
        optimizer=optimizer,
        metrics=metrics,
    )

    return model


def configure_keras_callbacks(
    checkpoints_dir,
    hypertune,
    hypertune_kwargs,
    earlystopping,
    earlystopping_kwargs,
):
    callbacks = []

    logging.info("Use HyperParametersTuning")
    if hypertune:
        callbacks.append(HyperTuneCallback(**hypertune_kwargs))

    logging.info("Use ModelCheckpointing")
    if checkpoints_dir:
        callbacks.append(
            tf.keras.callbacks.ModelCheckpoint(
                checkpoints_dir, save_weights_only=True, verbose=1
            )
        )

    logging.info("Use early stopping")
    if earlystopping:
        callbacks.append(
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss", mode="min", patience=earlystopping_kwargs
            )
        )

    return callbacks


def get_distribution_strategy(distribute_strategy: str) -> tf.distribute.Strategy:
    """Set distribute strategy based on input string.
    Args:
        distribute_strategy (str): single, mirror or multi
    Returns:
        strategy (tf.distribute.Strategy): distribution strategy
    """
    logging.info(f"Distribution strategy: {distribute_strategy}")

    # Single machine, single compute device
    if distribute_strategy == "single":
        if len(tf.config.list_physical_devices("GPU")):
            strategy = tf.distribute.OneDeviceStrategy(device="/gpu:0")
        else:
            strategy = tf.distribute.OneDeviceStrategy(device="/cpu:0")
    # Single machine, multiple compute device
    elif distribute_strategy == "mirror":
        strategy = tf.distribute.MirroredStrategy()
    # Multiple machine, multiple compute device
    elif distribute_strategy == "multi":
        strategy = tf.distribute.MultiWorkerMirroredStrategy()
    else:
        raise RuntimeError(f"Distribute strategy: {distribute_strategy} not supported")
    return strategy


def _is_chief(strategy: tf.distribute.Strategy) -> bool:
    """Determine whether current worker is the chief (master). See more info:
    - https://www.tensorflow.org/tutorials/distribute/multi_worker_with_keras
    - https://www.tensorflow.org/api_docs/python/tf/distribute/cluster_resolver/ClusterResolver # noqa: E501
    Args:
        strategy (tf.distribute.Strategy): strategy
    Returns:
        is_chief (bool): True if worker is chief, otherwise False
    """
    cr = strategy.cluster_resolver
    return (cr is None) or (cr.task_type == "chief" and cr.task_id == 0)


def train_and_evaluate(params):
    if params["model"].startswith("gs://"):
        if params["metrics"] == "":
            gcs_path = params["model"][len("gs://") :]
            logging.info(f"gcs_path: {gcs_path}")
            length = len(gcs_path)
            gcs_path = gcs_path[: length - 6]
            logging.info(f"gcs_path.split('/'): {gcs_path}")
            metrics_directory = os.path.join(gcs_path, "metrics")
            logging.info(f"metrics_directory: {metrics_directory}")
            params["metrics"] = Path("/gcs/" + metrics_directory)
            logging.info(f"params['metrics'] bucket path: {params['metrics']}")

        params["model"] = Path("/gcs/" + params["model"][5:])

    if params["checkpoints"].startswith("gs://"):
        params["checkpoints"] = Path("/gcs/" + params["checkpoints"][5:])

    # Initialize hyperparameters with default values
    hparams = {**DEFAULT_HPARAMS, **params.get("hparams", {})}

    # Update hparams with command line arguments
    if params.get("batch_size"):
        hparams["batch_size"] = params["batch_size"]

    if params.get("learning_rate"):
        hparams["learning_rate"] = params["learning_rate"]

    logging.info(f"Using model hyper-parameters: {hparams}")

    label = hparams["label"]

    # Set distribute strategy before any TF operations
    strategy = get_distribution_strategy(hparams["distribute_strategy"])

    train_ds = create_dataset(params["train_data"], label, hparams)
    valid_ds = create_dataset(params["valid_data"], label, hparams)
    test_ds = create_dataset(params["test_data"], label, hparams)

    train_features = list(train_ds.element_spec[0].keys())
    valid_features = list(valid_ds.element_spec[0].keys())
    logging.info(f"Training feature names: {train_features}")
    logging.info(f"Validation feature names: {valid_features}")

    with strategy.scope():
        model = build_and_compile_model(train_ds, hparams)

    # steps_per_epoch = len(train_ds) // (hparams["batch_size"] * hparams["epochs"])
    # Define the callbacks

    callbacks = configure_keras_callbacks(
        checkpoints_dir=params["checkpoints"],
        hypertune=params.get("hypertune"),
        hypertune_kwargs=dict(metric="val_root_mean_squared_error"),
        earlystopping=True,
        earlystopping_kwargs=hparams["early_stopping_epochs"],
    )

    history = model.fit(
        train_ds,
        validation_data=valid_ds,
        batch_size=hparams["batch_size"],
        epochs=hparams["epochs"],
        # steps_per_epoch=max(1, steps_per_epoch),
        verbose=2,  # 0=silent, 1=progress bar, 2=one line per epoch
        callbacks=callbacks,
    )

    # only persist output files if current worker is chief
    if not _is_chief(strategy):
        logging.info("not chief node, exiting now")
        sys.exit()

    logging.info(f"Save model to: {params['model']}")
    if not os.path.exists(params["model"]):
        logging.info(f"Create model directory : {params['model']}")
        params["model"].mkdir(parents=True)
    model.save(str(params["model"]), save_format="tf")

    eval_metrics = dict(zip(model.metrics_names, model.evaluate(test_ds)))

    metrics = {
        "problemType": "regression",
        "rootMeanSquaredError": eval_metrics["root_mean_squared_error"],
        "meanAbsoluteError": eval_metrics["mean_absolute_error"],
        "meanAbsolutePercentageError": eval_metrics["mean_absolute_percentage_error"],
        "rSquared": None,
        "rootMeanSquaredLogError": eval_metrics["mean_squared_logarithmic_error"],
    }

    if not os.path.exists(params["metrics"]):
        logging.info(f"Create metrics directory : {params['metrics']}")
        # Path(metrics_directory).mkdir(parents=True)
        os.makedirs(params["metrics"])

    logging.info(f"Save metrics to: {params['metrics']}")
    with open(os.path.join(params["metrics"], "metrics.json"), "w") as fh:
        json.dump(metrics, fh)

    # Persist URIs of training file(s) for model monitoring in batch predictions
    # See https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform_v1beta1.types.ModelMonitoringObjectiveConfig.TrainingDataset  # noqa: E501
    # for the expected schema.
    path = params["model"] / TRAINING_DATASET_INFO
    training_dataset_for_monitoring = {
        "gcsSource": {"uris": [params["train_data"]]},
        "dataFormat": "csv",
        "targetField": label,
    }
    logging.info(f"Save training dataset info for model monitoring: {path}")
    logging.info(f"Training dataset: {training_dataset_for_monitoring}")

    with open(path, "w") as fp:
        json.dump(training_dataset_for_monitoring, fp)

    return history
