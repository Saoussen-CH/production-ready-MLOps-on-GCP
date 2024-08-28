locals {
  cloudfunction_dir = "${path.module}/src"
  cloudfunction_files = fileset(local.cloudfunction_dir, "*")
  file_hashes = [for f in local.cloudfunction_files : filemd5("${local.cloudfunction_dir}/${f}")]
  cloudrunfunction_hash = md5(join("-", local.file_hashes))
}

data "archive_file" "function_archive" {
  type        = "zip"
  source_dir  = local.cloudfunction_dir
  output_path = "${var.function_name}_${local.cloudrunfunction_hash}.zip"
}

resource "google_storage_bucket_object" "archive" {
  name   = data.archive_file.function_archive.output_path
  bucket = var.gcf_source_bucket
  source = data.archive_file.function_archive.output_path
}

resource "google_cloudfunctions2_function" "default" {
  project                       = var.project_id
  location                      = var.region
  name                          = var.function_name
  description                   = var.description

  build_config {
    runtime     = var.runtime
    entry_point = var.entry_point
    environment_variables = merge(var.environment_variables, {
      PIPELINE_CONFIG = jsonencode(var.pipeline_config)
    })
    source {
      storage_source {
        bucket = google_storage_bucket_object.archive.bucket
        object = google_storage_bucket_object.archive.name
      }
    }
  }

  service_config {
    max_instance_count = var.max_instances
    available_memory   = var.available_memory_mb
    timeout_seconds    = var.timeout
    service_account_email = var.crf_service_account
  }

 event_trigger {
    trigger_region = var.region
    event_type = "google.cloud.audit.log.v1.written"
    retry_policy = "RETRY_POLICY_DO_NOT_RETRY"  # Disable retry on failure
    service_account_email = var.crf_service_account

    event_filters {
      attribute = "serviceName"
      value = "bigquery.googleapis.com"
    }

    event_filters {
      attribute = "methodName"
      value = "google.cloud.bigquery.v2.JobService.InsertJob"
    }

    event_filters {
      attribute = "resourceName"
      value = "/projects/${var.project_id}/datasets/${var.dataset_id}/tables/${var.table_id}"
    }
  }
}



output "function_uri" {
  value = google_cloudfunctions2_function.default.service_config[0].uri
}
