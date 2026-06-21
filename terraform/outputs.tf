output "service_url" {
  description = "The public HTTPS URL of the deployed Tesla Solar Sync Cloud Run service."
  value       = google_cloud_run_v2_service.solar_sync.uri
}

output "artifact_registry_repository_url" {
  description = "The repository URL where the Docker container image must be pushed."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}"
}

output "gcs_data_bucket_name" {
  description = "The Google Cloud Storage bucket name used for FUSE persistent database storage."
  value       = google_storage_bucket.data_bucket.name
}

output "service_account_email" {
  description = "The email address of the IAM Service Account used by the Cloud Run container."
  value       = google_service_account.cloud_run_sa.email
}
