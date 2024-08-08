

output "pipeline_root_bucket_name" {
  value = google_storage_bucket.pipeline_root_bucket.name
}

output "vertex_pipelines_sa_email" {
  value = google_service_account.pipelines_sa.email
}
