## Google Cloud APIs to enable ##
resource "google_project_service" "gcp_services" {
  for_each                   = toset(var.gcp_service_list)
  project                    = var.project_id
  service                    = each.key
  disable_on_destroy         = var.disable_services_on_destroy
  disable_dependent_services = var.disable_dependent_services
}

## Service Accounts ##

# Vertex Pipelines service account
resource "google_service_account" "pipelines_sa" {
  project      = var.project_id
  account_id   = "vertex-pipelines"
  display_name = "Vertex Pipelines Service Account"
  depends_on   = [google_project_service.gcp_services]
}

# Cloud Run Function service account
resource "google_service_account" "vertex_cloudrunfunction_sa" {
  project      = var.project_id
  account_id   = "vertex-cloudrunfunction-sa"
  display_name = "Cloud Run Function (Vertex Pipeline trigger) Service Account"
  depends_on   = [google_project_service.gcp_services]
}

## GCS buckets ##

# Vertex Pipelines root bucket
resource "google_storage_bucket" "pipeline_root_bucket" {
  name                        = "${var.project_id}-pl-root"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  depends_on                  = [google_project_service.gcp_services]
}

# Cloud Run Function bucket
resource "google_storage_bucket" "gcf_source_bucket" {
  name                        = "${var.project_id}-gcf-source"
  location                    = local.cloudrunfunction_region
  project                     = var.project_id
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  depends_on                  = [google_project_service.gcp_services]
}

## Vertex Metadata store ##
resource "google_vertex_ai_metadata_store" "default_metadata_store" {
  provider    = google-beta
  name        = "default"
  description = "Default metadata store"
  project     = var.project_id
  region      = var.region
  depends_on  = [google_project_service.gcp_services]
}

## Artifact Registry - docker container images ##
resource "google_artifact_registry_repository" "mlops_docker_repo" {
  repository_id = "mlops-docker-repo"
  description   = "Container image repository for training container images"
  project       = var.project_id
  location      = var.region
  format        = "DOCKER"
  depends_on    = [google_project_service.gcp_services]
}

## Artifact Registry - KFP pipelines ##
resource "google_artifact_registry_repository" "mlops_pipeline_repo" {
  repository_id = "mlops-pipeline-repo"
  description   = "KFP repository for Vertex Pipelines"
  project       = var.project_id
  location      = var.region
  format        = "KFP"
  depends_on    = [google_project_service.gcp_services]
}


## Cloud Function - used to trigger pipelines ##

locals {
  cloudrunfunction_region = coalesce(var.cloudrunfunction_region, var.region)
}



resource "google_pubsub_topic" "pipeline_completion" {
  name    = "pipeline-completion"
  project = var.project_id
  depends_on = [google_project_service.gcp_services]
}

resource "google_pubsub_subscription" "pipeline_completion_subscription" {
  name    = "pipeline-completion-subscription"
  topic   = google_pubsub_topic.pipeline_completion.id
  project = var.project_id

  push_config {
    push_endpoint = module.cloudrunfunction.function_uri
  }
}



# Cloud Run Function (for triggering pipelines)
module "cloudrunfunction" {
  source               = "../../modules/cloudrunfunction"
  project_id           = var.project_id
  region               = local.cloudrunfunction_region
  function_name        = var.function_name
  description          = var.description
  runtime              = var.runtime
  entry_point          = var.entry_point
  crf_service_account  = google_service_account.vertex_cloudrunfunction_sa.email
  gcf_source_bucket    = google_storage_bucket.gcf_source_bucket.name
  max_instances        = var.max_instances
  available_memory_mb  = var.available_memory_mb
  timeout              = var.timeout
  dataset_id           = var.dataset_id
  table_id             = var.table_id
  pipeline_config = {
    project                  = var.project_id
    location                 = var.region
    base_output_dir          = google_storage_bucket.pipeline_root_bucket.url
    training_template_path   = var.training_template_path
    prediction_template_path = var.prediction_template_path
    display_name             = "mlops-pipeline"
    bq_location              = "US"
    use_latest_data          = var.use_latest_data
    timestamp                = var.timestamp
    pubsub_topic_name        = google_pubsub_topic.pipeline_completion.name
    type                     = "training"
  }
}
