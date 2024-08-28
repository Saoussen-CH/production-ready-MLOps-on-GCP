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
  default = ""
}

variable "use_latest_data" {
  description = "Flag to determine whether to use the latest data."
  type        = string
}
