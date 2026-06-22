output "service_url" {
  description = "The public URL of the deployed Tesla Solar Sync FastAPI application."
  value       = google_cloud_run_v2_service.solar_sync.uri
}

output "service_location" {
  description = "The region of the deployed Cloud Run service."
  value       = google_cloud_run_v2_service.solar_sync.location
}
