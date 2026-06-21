output "data_bucket_name" {
  description = "The name of the GCS bucket used for storage."
  value       = google_storage_bucket.data_bucket.name
}

output "cloud_run_sa_email" {
  description = "The email of the Cloud Run service account."
  value       = google_service_account.cloud_run_sa.email
}

output "vault_secret_id" {
  description = "The secret ID for the AES vault secret."
  value       = google_secret_manager_secret.vault_secret.secret_id
}

output "tesla_email_id" {
  description = "The secret ID for the Tesla email secret."
  value       = google_secret_manager_secret.tesla_email.secret_id
}
