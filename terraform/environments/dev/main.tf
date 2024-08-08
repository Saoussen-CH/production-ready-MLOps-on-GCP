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
  #backend "gcs" {}
}

resource "random_id" "default" {
  byte_length = 8
}

resource "google_storage_bucket" "default" {
  name     = "${var.project_id}-terraform-remote-backend"
  location = "US"

  force_destroy               = false
  public_access_prevention    = "enforced"
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

resource "local_file" "default" {
  file_permission = "0644"
  filename        = "${path.module}/backend.tf"

  # You can store the template in a file and use the templatefile function for
  # more modularity, if you prefer, instead of storing the template inline as
  # we do here.
  content = <<-EOT
  terraform {
    backend "gcs" {
      bucket = "${google_storage_bucket.default.name}"
    }
  }
  EOT
}

# Core Vertex Pipelines infrastructure
module "vertex_deployment" {
  source     = "../../modules/vertex_deployment"
  project_id = var.project_id
  region     = var.region
}
