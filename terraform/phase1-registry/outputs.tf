output "registry_id" {
  description = "The ID of the created Artifact Registry repository."
  value       = google_artifact_registry_repository.docker_repo.id
}

output "registry_name" {
  description = "The name of the created Artifact Registry repository."
  value       = google_artifact_registry_repository.docker_repo.name
}

output "registry_url" {
  description = "The fully qualified URL to push docker images to."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}"
}
