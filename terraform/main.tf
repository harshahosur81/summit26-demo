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

# 1. Enable Required GCP APIs
locals {
  apis = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com"
  ]
}

resource "google_project_service" "enabled_apis" {
  for_each                   = toset(local.apis)
  project                    = var.project_id
  service                    = each.key
  disable_on_destroy         = false
  disable_dependent_services = false
}

# 2. Artifact Registry for Container Storage
resource "google_artifact_registry_repository" "docker_repo" {
  depends_on    = [google_project_service.enabled_apis]
  location      = var.region
  repository_id = "solar-sync-registry"
  description   = "Docker container repository for Tesla Solar Sync app"
  format        = "DOCKER"
}

# 3. GCS Bucket for Durable SQLite SQLite Database (FUSE Mount)
resource "google_storage_bucket" "data_bucket" {
  depends_on                  = [google_project_service.enabled_apis]
  name                        = "${var.project_id}-solar-sync-data"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# 4. Dedicated Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  depends_on   = [google_project_service.enabled_apis]
  account_id   = "solar-sync-runner"
  display_name = "Tesla Solar Sync Cloud Run Service Account"
}

# 5. GCS Bucket Access Binding (SA read/write)
resource "google_storage_bucket_iam_member" "bucket_access" {
  bucket = google_storage_bucket.data_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# 6. Secret Manager: AES Cryptographic Vault Key
resource "google_secret_manager_secret" "vault_secret" {
  depends_on = [google_project_service.enabled_apis]
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

# 7. Secret Manager: Tesla SSO Account Email
resource "google_secret_manager_secret" "tesla_email" {
  depends_on = [google_project_service.enabled_apis]
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

# 8. Cloud Run Service (v2 API for FUSE GCS Mounting)
resource "google_cloud_run_v2_service" "solar_sync" {
  depends_on = [
    google_project_service.enabled_apis,
    google_artifact_registry_repository.docker_repo,
    google_secret_manager_secret_iam_member.sa_vault_secret_accessor,
    google_secret_manager_secret_iam_member.sa_tesla_email_accessor,
    google_storage_bucket_iam_member.bucket_access
  ]

  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloud_run_sa.email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/solar-sync-app:${var.image_tag}"
      
      ports {
        container_port = 8888
      }

      # Standard Environments
      env {
        name  = "PORT"
        value = "8888"
      }
      env {
        name  = "GRID_PHASES"
        value = tostring(var.grid_phases)
      }
      env {
        name  = "EMA_ALPHA"
        value = tostring(var.ema_alpha)
      }
      env {
        name  = "OVERRIDE_DURATION_MINS"
        value = tostring(var.override_duration_mins)
      }
      env {
        name  = "INVERTER_IP"
        value = var.inverter_ip
      }

      # Secured Environments from Secret Manager
      env {
        name = "VAULT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.vault_secret.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "TESLA_EMAIL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.tesla_email.secret_id
            version = "latest"
          }
        }
      }

      # Mount persistence FUSE directory
      volume_mounts {
        name       = "solar-sync-data"
        mount_path = "/app/src/backend/data"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1024Mi"
        }
      }
    }

    # FUSE Mount Specification
    volumes {
      name = "solar-sync-data"
      gcs {
        bucket    = google_storage_bucket.data_bucket.name
        read_only = false
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# 9. Allow Public Access to the Steampunk Dashboard (allUsers Invoker)
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = google_cloud_run_v2_service.solar_sync.project
  location = google_cloud_run_v2_service.solar_sync.location
  name     = google_cloud_run_v2_service.solar_sync.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
