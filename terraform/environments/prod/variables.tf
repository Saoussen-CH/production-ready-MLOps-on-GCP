variable "project_id" {
  description = "The ID of the project in which to provision resources."
  type        = string
}

variable "region" {
  description = "Google Cloud region to use for resources and Vertex Pipelines execution."
  type        = string
}

variable "prediction_template_path" {
  description = "GCS path to the Vertex AI prediction pipeline template."
  type        = string
}

variable "training_template_path" {
  description = "GCS path to the Vertex AI training pipeline template."
  type        = string
}

variable "timestamp" {
  description = "Timestamp for the pipeline execution."
  type        = string
}

variable "use_latest_data" {
  description = "Flag to determine whether to use the latest data."
  type        = string
}

variable "dataset_id" {
  type = string
  description = "The ID of the BigQuery dataset containing the target table."
}

variable "table_id" {
  type = string
  description = "The ID of the BigQuery table where row insertions will trigger the function."
}
