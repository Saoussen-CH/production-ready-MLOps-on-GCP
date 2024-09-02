variable "project_id" {
  description = "The ID of the Google Cloud project in which to provision resources."
  type        = string
}

variable "region" {
  description = "Google Cloud region to use for resources and Vertex Pipelines execution."
  type        = string
}

variable "cloudrunfunction_region" {
  description = "Google Cloud region to use for the Cloud Run Function (and CRF staging bucket). Defaults to the same as var.region"
  type        = string
  default     = null
}

variable "cloudrunfunction_name" {
  description = "Name of the Cloud Run Function"
  type        = string
  default     = "vertex-pipelines-trigger"
}

variable "cloudrunfunction_description" {
  description = "Description for the Cloud Function"
  type        = string
  default     = "Cloud Run function to trigger Vertex AI pipeline when new data arrives in BigQuery"
}

variable "gcp_service_list" {
  description = "List of Google Cloud APIs to enable on the project."
  type        = list(string)
  default = [
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "bigquerydatatransfer.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "dataflow.googleapis.com",
    "eventarc.googleapis.com",
    "iam.googleapis.com",
    "monitoring.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "storage-api.googleapis.com",
    "storage-component.googleapis.com",
    "storage.googleapis.com",
  ]
}

variable "disable_services_on_destroy" {
  description = "If true, disable the service when the Terraform resource is destroyed. Defaults to true. May be useful in the event that a project is long-lived but the infrastructure running in that project changes frequently."
  type        = bool
  default     = true
}

variable "disable_dependent_services" {
  description = "If true, services that are enabled and which depend on this service should also be disabled when this service is destroyed. If false or unset, an error will be generated if any enabled services depend on this service when destroying it."
  type        = bool
  default     = true
}

variable "pipelines_sa_project_roles" {
  description = "List of project IAM roles to be granted to the Vertex Pipelines service account."
  type        = list(string)
  default = [
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/artifactregistry.reader"
  ]
}

variable "cloudrunfunction_sa_project_roles" {
  description = "List of project IAM roles to be granted to the Cloud Run Function service account."
  type        = list(string)
  default = [
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/artifactregistry.reader",
    "roles/iam.serviceAccountUser",
    "roles/eventarc.admin",
    "roles/cloudfunctions.admin",
    "roles/pubsub.editor",
    "roles/pubsub.subscriber",
    "roles/eventarc.eventReceiver",
    "roles/aiplatform.serviceAgent"
  ]
}

variable "function_name" {
  description = "The name of the Cloud Run Function."
  type        = string
  default     = "vertex-cloudrunfunction"
}

variable "description" {
  description = "The description of the Cloud Run Function."
  type        = string
  default     = "Cloud Run Function to trigger Vertex AI Pipelines."
}

variable "runtime" {
  description = "Runtime for Cloud Run Function."
  type        = string
  default     = "python310"
}

variable "entry_point" {
  description = "Entry point of the function."
  type        = string
  default     = "mlops_entrypoint"
}

variable "max_instances" {
  description = "Maximum instances for Cloud Run Function."
  type        = number
  default     = 5
}

variable "available_memory_mb" {
  description = "Memory allocated for the function in MB."
  type        = string
  default     = "256 Mi"
}

variable "timeout" {
  description = "Execution timeout for the Cloud Run Function in seconds."
  type        = number
  default     = 300
}

variable "training_template_path" {
  description = "GCS path to the Vertex AI training pipeline template."
  type        = string
}

variable "prediction_template_path" {
  description = "GCS path to the Vertex AI prediction pipeline template."
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
