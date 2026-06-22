variable "project_id" {
  description = "The Google Cloud Project ID where resources will be deployed."
  type        = string
}

variable "region" {
  description = "The Google Cloud region where resources will be deployed."
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "The name of the Cloud Run service."
  type        = string
  default     = "tesla-solar-sync"
}

variable "vault_secret" {
  description = "The 32-character secure AES vault secret (key derived via PBKDF2)."
  type        = string
  sensitive   = true
}

variable "tesla_email" {
  description = "Registered Tesla Account Email. Set to 'user@example.com' to run in Mock Mode initially."
  type        = string
  default     = "user@example.com"
}

variable "inverter_ip" {
  description = "Local IP address of the GoodWe hybrid inverter. If blank or unreachable, dynamic GoodWe emulator engages."
  type        = string
  default     = ""
}

variable "grid_phases" {
  description = "Grid connection phases scheme (1 or 3 phases)."
  type        = number
  default     = 3
}

variable "ema_alpha" {
  description = "EMA smoothing coefficient alpha [0.01 - 1.0]."
  type        = number
  default     = 0.1
}

variable "override_duration_mins" {
  description = "The default duration the manual override remains active before reverting to auto-tracking."
  type        = number
  default     = 120
}

variable "image_tag" {
  description = "The container image tag to deploy."
  type        = string
  default     = "latest"
}
