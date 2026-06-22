variable "project_id" {
  description = "The Google Cloud Project ID where resources will be deployed."
  type        = string
}

variable "region" {
  description = "The Google Cloud region where resources will be deployed."
  type        = string
  default     = "australia-southeast1"
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
