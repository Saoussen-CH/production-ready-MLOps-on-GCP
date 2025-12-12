# MLOps Architecture on GCP

This document contains Mermaid diagrams illustrating the architecture of the production-ready MLOps solution.

## Overall System Architecture

```mermaid
graph TB
    subgraph "GitHub Repository"
        Code[Code Repository]
        PR[Pull Requests]
        Release[Git Tags/Releases]
    end

    subgraph "GCP Admin Project - CI/CD"
        CB[Cloud Build]
        CB_PR[PR Checks Trigger]
        CB_E2E[E2E Test Trigger]
        CB_TF_Plan[Terraform Plan Trigger]
        CB_TF_Apply[Terraform Apply Trigger]
        CB_Release[Release Trigger]
        CB_Schedule[Schedule Trigger]
    end

    subgraph "GCP Dev Project"
        Dev_AR[Artifact Registry]
        Dev_Vertex[Vertex AI Pipelines]
        Dev_BQ[BigQuery]
        Dev_GCS[Cloud Storage]
        Dev_Registry[Model Registry]
    end

    subgraph "GCP Test Project"
        Test_AR[Artifact Registry]
        Test_Vertex[Vertex AI Pipelines]
        Test_BQ[BigQuery]
        Test_GCS[Cloud Storage]
        Test_Registry[Model Registry]
    end

    subgraph "GCP Prod Project"
        Prod_AR[Artifact Registry]
        Prod_Vertex[Vertex AI Pipelines]
        Prod_BQ[BigQuery]
        Prod_GCS[Cloud Storage]
        Prod_Registry[Model Registry]
        Prod_CRF[Cloud Run Function]
        Prod_PubSub[Pub/Sub]
    end

    Code --> PR
    PR --> CB_PR
    PR --> CB_TF_Plan
    PR --> CB_E2E
    Code --> Release
    Release --> CB_Release

    CB_PR --> |Pre-commit checks| CB
    CB_E2E --> |Run E2E tests| Dev_Vertex
    CB_TF_Plan --> |Plan infrastructure| CB
    CB_TF_Apply --> |Deploy infrastructure| Dev_AR
    CB_TF_Apply --> |Deploy infrastructure| Test_AR
    CB_TF_Apply --> |Deploy infrastructure| Prod_AR

    CB_Release --> |Build & push images| Dev_AR
    CB_Release --> |Build & push images| Test_AR
    CB_Release --> |Build & push images| Prod_AR

    CB_Schedule --> |Create schedules| Test_Vertex
    CB_Schedule --> |Create schedules| Prod_Vertex

    Prod_CRF --> |Trigger pipelines| Prod_Vertex
    Prod_PubSub --> |Notify completion| Prod_CRF

    style CB fill:#4285f4
    style Dev_Vertex fill:#34a853
    style Test_Vertex fill:#fbbc04
    style Prod_Vertex fill:#ea4335
```

## Training Pipeline Architecture

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

## Prediction Pipeline Architecture

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

## CI/CD Pipeline Flow

```mermaid
graph TB
    subgraph "Developer Workflow"
        Dev[Developer]
        Branch[Feature Branch]
        Commit[Commit Changes]
        Push[Push to GitHub]
    end

    subgraph "Pull Request Stage"
        PR[Create Pull Request]
        PRChecks[pr-checks.yaml]
        E2E[e2e-test.yaml<br/>Manual /gcbrun]
        TFPlan[terraform-plan.yaml]
    end

    subgraph "Validation"
        PreCommit[Pre-commit Hooks<br/>Linting, Formatting]
        UnitTest[Unit Tests<br/>Components & Pipelines]
        Compile[Pipeline Compilation]
        E2ETest[E2E Pipeline Test<br/>in Dev Environment]
        TFValidate[Terraform Plan<br/>Preview Changes]
    end

    subgraph "Merge & Release"
        Merge[Merge to Main]
        TFApply[terraform-apply.yaml<br/>Deploy Infrastructure]
        Tag[Create Git Tag]
        Release[release.yaml]
    end

    subgraph "Deployment"
        BuildImage[Build Docker Images]
        PushAR[Push to Artifact Registry]
        CompilePipeline[Compile Pipelines]
        UploadPipeline[Upload to AR - KFP Repo]
        Schedule[schedule-pipelines.yaml<br/>Manual Trigger]
        CreateSchedule[Create Pipeline Schedules]
    end

    subgraph "Environments"
        DevEnv[Dev Environment]
        TestEnv[Test Environment]
        ProdEnv[Prod Environment]
    end

    Dev --> Branch
    Branch --> Commit
    Commit --> Push
    Push --> PR

    PR --> PRChecks
    PR --> E2E
    PR --> TFPlan

    PRChecks --> PreCommit
    PRChecks --> UnitTest
    PRChecks --> Compile

    E2E --> E2ETest
    TFPlan --> TFValidate

    PR --> |Approved| Merge
    Merge --> TFApply
    TFApply --> DevEnv
    TFApply --> TestEnv
    TFApply --> ProdEnv

    Merge --> Tag
    Tag --> Release

    Release --> BuildImage
    BuildImage --> PushAR
    Release --> CompilePipeline
    CompilePipeline --> UploadPipeline

    UploadPipeline --> Schedule
    Schedule --> CreateSchedule

    CreateSchedule --> TestEnv
    CreateSchedule --> ProdEnv

    style PRChecks fill:#4285f4
    style E2E fill:#34a853
    style Release fill:#fbbc04
    style TFApply fill:#ea4335
```

## Infrastructure Components (Terraform)

```mermaid
graph TB
    subgraph "Terraform Modules"
        Main[Main Configuration]
        VertexMod[vertex_deployment Module]
        CRFMod[cloudrunfunction Module]
    end

    subgraph "GCP Resources - Per Environment"
        APIs[Enable APIs<br/>Vertex AI, BigQuery,<br/>Storage, Artifact Registry]
        SA_Pipeline[Service Account<br/>Vertex Pipelines]
        SA_CRF[Service Account<br/>Cloud Run Function]
        Bucket_Root[GCS Bucket<br/>Pipeline Root]
        Bucket_CRF[GCS Bucket<br/>Function Source]
        AR_Docker[Artifact Registry<br/>Docker Repository]
        AR_KFP[Artifact Registry<br/>KFP Repository]
        Metadata[Vertex AI<br/>Metadata Store]
        PubSub_Topic[Pub/Sub Topic<br/>Pipeline Notifications]
        CloudRun[Cloud Run Function<br/>Pipeline Trigger]
    end

    subgraph "IAM Permissions"
        IAM_Vertex[Vertex AI Roles]
        IAM_BQ[BigQuery Roles]
        IAM_Storage[Storage Roles]
        IAM_AR[Artifact Registry Roles]
    end

    Main --> VertexMod
    Main --> CRFMod

    VertexMod --> APIs
    VertexMod --> SA_Pipeline
    VertexMod --> SA_CRF
    VertexMod --> Bucket_Root
    VertexMod --> Bucket_CRF
    VertexMod --> AR_Docker
    VertexMod --> AR_KFP
    VertexMod --> Metadata

    CRFMod --> PubSub_Topic
    CRFMod --> CloudRun

    SA_Pipeline --> IAM_Vertex
    SA_Pipeline --> IAM_BQ
    SA_Pipeline --> IAM_Storage
    SA_Pipeline --> IAM_AR

    style VertexMod fill:#4285f4
    style CRFMod fill:#34a853
    style SA_Pipeline fill:#fbbc04
    style CloudRun fill:#ea4335
```

## Data Flow - Training Pipeline

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant GH as GitHub
    participant CB as Cloud Build
    participant AR as Artifact Registry
    participant Vertex as Vertex AI Pipelines
    participant BQ as BigQuery
    participant GCS as Cloud Storage
    participant Train as Custom Training Job
    participant Reg as Model Registry

    Dev->>GH: Push git tag (v1.2)
    GH->>CB: Trigger release.yaml
    CB->>CB: Build training container
    CB->>AR: Push container image
    CB->>CB: Compile training pipeline
    CB->>AR: Upload pipeline to KFP repo

    Dev->>CB: Trigger schedule-pipelines.yaml
    CB->>Vertex: Create pipeline schedule

    Vertex->>BQ: Execute preprocessing SQL
    BQ->>GCS: Extract train/val/test data
    Vertex->>Vertex: Start hyperparameter tuning
    Vertex->>Train: Launch 6 trials (2 parallel)
    Train->>Train: Train with different hyperparams
    Train->>Vertex: Return best hyperparameters
    Vertex->>Train: Train final model
    Train->>GCS: Save model artifacts
    Vertex->>Reg: Lookup champion model
    Vertex->>Vertex: Compare RMSE metrics
    alt Challenger better than Champion
        Vertex->>Reg: Upload new champion model
    else Champion still best
        Vertex->>Vertex: Keep existing champion
    end
```

## Data Flow - Prediction Pipeline

```mermaid
sequenceDiagram
    participant CRF as Cloud Run Function
    participant PubSub as Pub/Sub
    participant Vertex as Vertex AI Pipelines
    participant Reg as Model Registry
    participant BQ as BigQuery
    participant Batch as Batch Prediction Job
    participant Monitor as Model Monitoring
    participant Alert as Email Alerts

    Note over CRF: Triggered by new data or schedule

    CRF->>Vertex: Trigger prediction pipeline
    Vertex->>Reg: Lookup default (champion) model
    Reg-->>Vertex: Return model resource
    Vertex->>BQ: Execute preprocessing SQL
    BQ-->>Vertex: Preprocessed data ready
    Vertex->>Batch: Start batch prediction job
    Batch->>BQ: Read input table
    Batch->>Batch: Generate predictions
    Batch->>BQ: Write predictions output
    Vertex->>Monitor: Check for data skew
    Monitor->>Monitor: Compare training vs serving data

    alt Skew detected
        Monitor->>Alert: Send email alert
    end

    Vertex->>PubSub: Publish completion event
    PubSub-->>CRF: Notify completion
```

## Component Interaction

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

## Multi-Environment Strategy

```mermaid
graph LR
    subgraph "Code Repository"
        Main[Main Branch]
        Develop[Develop Branch]
        Feature[Feature Branches]
    end

    subgraph "Dev Environment"
        Dev_Infra[Infrastructure<br/>Terraform]
        Dev_Pipeline[Pipeline Execution<br/>E2E Testing]
        Dev_Model[Model Experiments]
    end

    subgraph "Test Environment"
        Test_Infra[Infrastructure<br/>Terraform]
        Test_Pipeline[Pipeline Execution<br/>Scheduled]
        Test_Model[Model Validation]
    end

    subgraph "Prod Environment"
        Prod_Infra[Infrastructure<br/>Terraform]
        Prod_Pipeline[Pipeline Execution<br/>Scheduled + Event]
        Prod_Model[Champion Models]
    end

    Feature --> |PR| Main
    Main --> |Terraform Apply| Dev_Infra
    Main --> |Terraform Apply| Test_Infra
    Main --> |Terraform Apply| Prod_Infra

    Main --> |Release Tag| Dev_Pipeline
    Main --> |Release Tag| Test_Pipeline
    Main --> |Release Tag| Prod_Pipeline

    Dev_Pipeline --> |Validation| Test_Pipeline
    Test_Pipeline --> |Promotion| Prod_Pipeline

    style Dev_Infra fill:#34a853
    style Test_Infra fill:#fbbc04
    style Prod_Infra fill:#ea4335
```
