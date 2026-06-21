variable "project_id" {
  description = "The Google Cloud Project ID where resources will be deployed."
  type        = string
}

variable "region" {
  description = "The Google Cloud region where resources will be deployed."
  type        = string
  default     = "australia-southeast1"
}
