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
    bucket = "devlp-431918-tfstate"
  }
}


# Core Vertex Pipelines infrastructure
module "vertex_deployment" {
  source     = "../../modules/vertex_deployment"
  project_id = var.project_id
  region     = var.region
}
