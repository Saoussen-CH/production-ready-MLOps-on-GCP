training_template_path      = "https://us-central1-kfp.pkg.dev/${var.project_id}/mlops-pipeline-repo/taxifare-training-pipeline/v1.1.0"
prediction_template_path    = "https://us-central1-kfp.pkg.dev/groovy-pager-431918-c8/mlops-pipeline-repo/taxifare-batch-prediction-pipeline/v1.1.0"
use_latest_data             = true
timestamp                   = ""
dataset_id                  = "taxi_trips_dataset"
table_id                    = "preprocessed_data"
