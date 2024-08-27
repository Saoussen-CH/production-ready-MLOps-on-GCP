variable "project_id" {
  description = "The ID of the Google Cloud project in which to provision resources."
  type        = string
}

variable "region" {
  description = "Google Cloud region to use for resources and Vertex Pipelines execution."
  type        = string
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
    "iam.googleapis.com",
    "monitoring.googleapis.com",
    "pubsub.googleapis.com",
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
  ]
}

variable "service_account_email" {
  description = "The service account email"
  type        = string
}