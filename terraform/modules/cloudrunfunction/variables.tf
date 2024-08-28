variable "project_id" {
  description = "The ID of the project where the cloud run function will be deployed."
  type        = string
}

variable "region" {
  description = "Region of the cloud runfunction."
  type        = string
}

variable "function_name" {
  description = "Name of the cloud run function"
  type        = string
}

variable "description" {
  description = "Description of the cloud run function."
  type        = string
  default     = "Cloud Run function to trigger Vertex AI pipeline when new data arrives in BigQuery"
}

variable "runtime" {
  description = "The runtime in which the function will be executed."
  type        = string
}


variable "entry_point" {
  description = "The name of a method in the function source which will be invoked when the function is executed."
  type        = string
  default     = null
}

variable "gcf_source_bucket" {
  description = "The name of the bucket to use for staging the Cloud Run Function code."
  type        = string
}

variable "max_instances" {
  description = "The maximum number of parallel executions of the function."
  type        = number
  default     = null
}


variable "crf_service_account" {
  description = "The service account (email address) to run the function as."
  type        = string
}

variable "environment_variables" {
  description = "A set of key/value environment variable pairs to assign to the function."
  type        = map(string)
  default     = null
}

variable "build_environment_variables" {
  description = "A set of key/value environment variable pairs available during build time."
  type        = map(string)
  default     = null
}

variable "available_memory_mb" {
  description = "Memory (in MB), available to the cloud function."
  type        = string
  default     = null
}

variable "timeout" {
  description = "Timeout (in seconds) for the function. Default value is 60 seconds. Cannot be more than 540 seconds."
  type        = number
  default     = null
}


variable "pipeline_config" {
  description = "The configuration for the pipeline"
  type        = map(any)
  default     = {}
}

variable "dataset_id" {
  type = string
  description = "The ID of the BigQuery dataset containing the target table."
}

variable "table_id" {
  type = string
  description = "The ID of the BigQuery table where row insertions will trigger the function."
}
