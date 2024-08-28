output "pipeline_root_bucket_name" {
  value = google_storage_bucket.pipeline_root_bucket.name
}

output "vertex_pipelines_sa_email" {
  value = google_service_account.pipelines_sa.email
}

output "cloudrunfunction_sa_email" {
  value = google_service_account.vertex_cloudrunfunction_sa.email
}

output "gcf_source_bucket" {
  value = google_storage_bucket.gcf_source_bucket.name
}

output "google_pubsub_topic" {
  value = google_pubsub_topic.pipeline_completion
}

output "pipeline_completion" {
  value = google_pubsub_topic.pipeline_completion.id
}
