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

# Enable Required GCP APIs
locals {
  apis = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "cloudbuild.googleapis.com"
  ]
}

resource "google_project_service" "enabled_apis" {
  for_each                   = toset(local.apis)
  project                    = var.project_id
  service                    = each.key
  disable_on_destroy         = false
  disable_dependent_services = false
}

# Artifact Registry for Container Storage
resource "google_artifact_registry_repository" "docker_repo" {
  depends_on    = [google_project_service.enabled_apis]
  location      = var.region
  repository_id = "solar-sync-registry"
  description   = "Dedicated Docker container repository for Tesla Solar Sync app (summit26)"
  format        = "DOCKER"
}
