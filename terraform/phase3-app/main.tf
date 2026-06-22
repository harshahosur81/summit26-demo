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

# 1. Fetch Existing Supporting Infrastructure using Data Sources
data "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "solar-sync-registry"
}

data "google_storage_bucket" "data_bucket" {
  name = "${var.project_id}-solar-sync-data"
}

data "google_service_account" "cloud_run_sa" {
  account_id = "solar-sync-runner"
}

data "google_secret_manager_secret" "vault_secret" {
  secret_id = "SOLAR_SYNC_VAULT_SECRET"
}

data "google_secret_manager_secret" "tesla_email" {
  secret_id = "SOLAR_SYNC_TESLA_EMAIL"
}

# 2. Cloud Run Service (v2 API for FUSE GCS Mounting)
resource "google_cloud_run_v2_service" "solar_sync" {
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = data.google_service_account.cloud_run_sa.email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${data.google_artifact_registry_repository.docker_repo.repository_id}/solar-sync-app:${var.image_tag}"

      ports {
        container_port = 8888
      }

      # Standard Environments
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
            secret  = data.google_secret_manager_secret.vault_secret.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "TESLA_EMAIL"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.tesla_email.secret_id
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
        bucket    = data.google_storage_bucket.data_bucket.name
        read_only = false
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# 3. Allow Public Access to the Steampunk Dashboard (allUsers Invoker)
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = google_cloud_run_v2_service.solar_sync.project
  location = google_cloud_run_v2_service.solar_sync.location
  name     = google_cloud_run_v2_service.solar_sync.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
