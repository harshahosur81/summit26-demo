terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.50.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. GCS Bucket for SQLite Database State Persistence (FUSE Mount)
resource "google_storage_bucket" "data_bucket" {
  name                        = "${var.project_id}-solar-sync-data"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# 2. Dedicated Service Account for Cloud Run Application
resource "google_service_account" "cloud_run_sa" {
  account_id   = "solar-sync-runner"
  display_name = "Tesla Solar Sync Cloud Run Service Account"
}

# 3. GCS Bucket IAM Binding (SA Read/Write)
resource "google_storage_bucket_iam_member" "bucket_access" {
  bucket = google_storage_bucket.data_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# 4. Secret Manager: AES Cryptographic Vault Key
resource "google_secret_manager_secret" "vault_secret" {
  secret_id  = "SOLAR_SYNC_VAULT_SECRET"
  labels     = { app = "solar-sync" }

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "vault_secret_val" {
  secret      = google_secret_manager_secret.vault_secret.id
  secret_data = var.vault_secret
}

resource "google_secret_manager_secret_iam_member" "sa_vault_secret_accessor" {
  secret_id = google_secret_manager_secret.vault_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# 5. Secret Manager: Tesla SSO Account Email
resource "google_secret_manager_secret" "tesla_email" {
  secret_id  = "SOLAR_SYNC_TESLA_EMAIL"
  labels     = { app = "solar-sync" }

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "tesla_email_val" {
  secret      = google_secret_manager_secret.tesla_email.id
  secret_data = var.tesla_email
}

resource "google_secret_manager_secret_iam_member" "sa_tesla_email_accessor" {
  secret_id = google_secret_manager_secret.tesla_email.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}
