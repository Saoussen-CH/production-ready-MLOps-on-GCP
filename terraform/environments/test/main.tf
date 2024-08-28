terraform {
  required_version = ">= 1.9"
  required_providers {

    google = {
      source  = "hashicorp/google"
      version = "~> 5.30.0"
    }

    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.30.0"
    }


  }
  # Terraform state stored in GCS
  backend "gcs" {

  }
}


# Core Vertex Pipelines infrastructure
module "vertex_deployment" {
  source     = "../../modules/vertex_deployment"
  project_id = var.project_id
  region     = var.region

    # The following variables are now sourced from auto.tfvars
  prediction_template_path = var.prediction_template_path
  training_template_path   = var.training_template_path
  timestamp                = var.timestamp
  use_latest_data          = var.use_latest_data
  dataset_id               = var.dataset_id
  table_id                 = var.table_id
}
