## Training Pipeline Overview

This repository includes an example ML training pipeline that demonstrates a comprehensive end-to-end process for training a model using Google Cloud's Vertex AI. The pipeline is defined using Kubeflow Pipelines (KFP) and leverages components such as BigQuery, custom training containers, and hyperparameter tuning.

### Training Pipeline Architecture

```mermaid
graph LR
    subgraph "Data Layer"
        BQ_Raw[BigQuery<br/>Chicago Taxi Trips<br/>Raw Data]
        BQ_Processed[Processed Data]
    end

    subgraph "Training Pipeline - Kubeflow"
        Extract[Extract Table to GCS]
        Split[Data Splitting<br/>Train/Val/Test]
        Tune[Hyperparameter Tuning<br/>Vertex AI HyperTune]
        Train[Model Training<br/>Custom Container]
        Eval[Model Evaluation]
        Upload[Upload to Registry]
    end

    subgraph "Compute & Storage"
        GCS[Cloud Storage<br/>Artifacts]
        Custom[Custom Training<br/>TensorFlow Container]
        Registry[Vertex AI<br/>Model Registry]
    end

    subgraph "Model Selection"
        Champion[Champion Model]
        Challenger[Challenger Model]
        Compare[RMSE Comparison]
    end

    BQ_Raw --> |SQL Preprocessing| BQ_Processed
    BQ_Processed --> Extract
    Extract --> |CSV files| GCS
    GCS --> Split
    Split --> Tune
    Tune --> |Best hyperparameters| Train
    Train --> Custom
    Custom --> |Trained model| Eval
    Eval --> Compare
    Compare --> |If better| Upload
    Upload --> Registry
    Registry --> Champion
    Registry --> Challenger

    style BQ_Raw fill:#669df6
    style Tune fill:#fbbc04
    style Custom fill:#34a853
    style Registry fill:#ea4335
```

### Key Pipeline Steps

1. **Data Preprocessing**:
   - The pipeline begins by preprocessing raw data stored in BigQuery. The data is cleaned and prepared for model training, using SQL queries defined in the `queries` directory.

2. **Data Splitting**:
   - The preprocessed data is split into training, validation, and test sets using repeatable data splitting queries. These splits are essential for training and evaluating the model effectively.

3. **Data Extraction**:
   - The split datasets are extracted from BigQuery and stored in Google Cloud Storage (GCS). This ensures that the data is readily accessible for the training process.

4. **Hyperparameter Tuning**:
   - The pipeline includes a hyperparameter tuning step, which utilizes Vertex AI's Hyperparameter Tuning Job. Key hyperparameters such as learning rate and batch size are tuned to optimize model performance. The tuning process is defined by the `PARAMETER_SPEC` and `METRIC_SPEC`, and the results are used to configure the final training job.

5. **Model Training**:
   - Once the optimal hyperparameters are identified, the model is trained using a custom container image specified in the `Dockerfile`. The training job leverages the tuned hyperparameters to achieve the best possible model performance.

6. **Model Evaluation and Upload**:
   - After training, the model is evaluated against a champion model based on a primary metric (e.g., root mean squared error). The best-performing model is then uploaded to the Model Registry in Vertex AI, ready for deployment.

### Running the Training Pipeline

To run the training pipeline, you need to configure the environment and build the necessary containers:

1. **Set up your environment**:
   - Ensure you have the necessary environment variables set, such as `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `IMAGE_NAME`, and `IMAGE_TAG`.

2. **Build and push the training container**:
   - Use the following command to build and push the container image for model training:

   ```bash
   make build
   ```

3. **Compile and run the pipeline**:
   - Compile the pipeline and run it in Vertex AI:

   ```bash
   make training
   ```

### Component Interaction

The training and prediction pipelines leverage reusable Kubeflow components that interact with various GCP services:

```mermaid
graph TB
    subgraph "Reusable KFP Components"
        C1[extract_table_to_gcs_op]
        C2[get_training_args_dict_op]
        C3[get_workerpool_spec_op]
        C4[lookup_model_op]
        C5[upload_best_model_op]
        C6[model_batch_predict_op]
        C7[get_custom_job_results_op]
        C8[get_hyperparameter_tuning_results_op]
    end

    subgraph "Training Pipeline"
        TP[training.py]
    end

    subgraph "Prediction Pipeline"
        PP[prediction.py]
    end

    subgraph "GCP Services"
        BQ[BigQuery]
        GCS[Cloud Storage]
        Vertex[Vertex AI]
        Registry[Model Registry]
    end

    TP --> C1
    TP --> C2
    TP --> C3
    TP --> C5
    TP --> C7
    TP --> C8

    PP --> C1
    PP --> C4
    PP --> C6

    C1 --> BQ
    C1 --> GCS
    C4 --> Registry
    C5 --> Registry
    C6 --> Vertex
    C7 --> Vertex
    C8 --> Vertex

    style TP fill:#4285f4
    style PP fill:#34a853
    style C1 fill:#fbbc04
    style C4 fill:#fbbc04
    style C5 fill:#fbbc04
    style C6 fill:#fbbc04
```

## Prediction Pipeline Overview

The prediction pipeline performs batch inference using the champion model from the Model Registry. It includes data preprocessing, batch prediction, and model monitoring capabilities.

### Prediction Pipeline Architecture

```mermaid
graph LR
    subgraph "Input"
        NewData[New Data<br/>BigQuery Table]
    end

    subgraph "Prediction Pipeline - Kubeflow"
        Lookup[Lookup Champion Model]
        Preprocess[Data Preprocessing]
        BatchPredict[Batch Prediction Job]
        Monitor[Model Monitoring<br/>Skew Detection]
    end

    subgraph "Storage & Registry"
        Registry[Model Registry<br/>Champion Model]
        Predictions[Predictions<br/>BigQuery Output]
        Alerts[Email Alerts]
    end

    subgraph "Monitoring"
        Skew{Data Skew<br/>Detected?}
        Log[Cloud Logging]
    end

    NewData --> Preprocess
    Lookup --> Registry
    Registry --> |Get default model| BatchPredict
    Preprocess --> |Preprocessed data| BatchPredict
    BatchPredict --> Predictions
    BatchPredict --> Monitor
    Monitor --> Skew
    Skew --> |Yes| Alerts
    Skew --> |Metrics| Log

    style Registry fill:#ea4335
    style BatchPredict fill:#34a853
    style Monitor fill:#fbbc04
    style Alerts fill:#ff6d00
```

### Key Prediction Steps

1. **Model Lookup**:
   - The pipeline retrieves the default (champion) model from Vertex AI Model Registry.

2. **Data Preprocessing**:
   - New data is preprocessed using the same SQL queries used during training to ensure consistency.

3. **Batch Prediction**:
   - The Vertex AI Batch Prediction Job processes the preprocessed data using the champion model.
   - Predictions are written directly to a BigQuery output table.

4. **Model Monitoring**:
   - The pipeline monitors for training-serving skew by comparing data distributions.
   - Email alerts are sent if skew thresholds are exceeded.

### Running the Prediction Pipeline

To run the prediction pipeline:

```bash
make prediction
```
