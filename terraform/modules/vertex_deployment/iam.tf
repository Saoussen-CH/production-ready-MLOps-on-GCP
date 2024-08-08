## Project IAM roles ##

# Vertex Pipelines SA project roles
resource "google_project_iam_member" "pipelines_sa_project_roles" {
  for_each = toset(var.pipelines_sa_project_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.pipelines_sa.email}"
}

# Give pipelines SA access to objects
# in the pipeline_root bucket
resource "google_storage_bucket_iam_member" "pipelines_sa_pipeline_root_bucket_iam" {
  for_each = toset([
    "roles/storage.objectAdmin",
    "roles/storage.legacyBucketReader",
  ])
  bucket = google_storage_bucket.pipeline_root_bucket.name
  member = "serviceAccount:${google_service_account.pipelines_sa.email}"
  role   = each.value
}
