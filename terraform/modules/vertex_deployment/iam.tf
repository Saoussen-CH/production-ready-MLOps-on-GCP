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

# Give cloud run functions SA access to use the pipelines SA for triggering pipelines
resource "google_service_account_iam_member" "cloudrunfunction_sa_can_use_pipelines_sa" {
  service_account_id = google_service_account.pipelines_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.vertex_cloudrunfunction_sa.email}"
}

# Give cloud run functions SA access to KFP Artifact Registry to access compiled pipelines
resource "google_artifact_registry_repository_iam_member" "cloudrunfunction_sa_can_access_ar" {
  project    = google_artifact_registry_repository.mlops_pipeline_repo.project
  location   = google_artifact_registry_repository.mlops_pipeline_repo.location
  repository = google_artifact_registry_repository.mlops_pipeline_repo.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.vertex_cloudrunfunction_sa.email}"
}

# Give cloud Run functions SA access to pipeline root bucket to check it exists
resource "google_storage_bucket_iam_member" "cloudrunfunction_sa_can_get_pl_root_bucket" {
  bucket = google_storage_bucket.pipeline_root_bucket.name
  role   = "roles/storage.legacyBucketReader"
  member = "serviceAccount:${google_service_account.vertex_cloudrunfunction_sa.email}"
}

# Cloud Run Function SA project roles
resource "google_project_iam_member" "cloudrunfunction_sa_project_roles" {
  for_each = toset(var.cloudrunfunction_sa_project_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.vertex_cloudrunfunction_sa.email}"
}
