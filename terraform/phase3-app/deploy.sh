#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -e

# Resolve the absolute path of this script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "🚀 Starting Phase 3: Deploying Cloud Run Application"
echo "========================================================================"

# 1. Run Terraform Apply for Phase 3
echo -e "\n📦 Deploying Cloud Run Service with GCS FUSE Persistence..."
terraform apply -auto-approve

# 2. Extract Cloud Run URL output
SERVICE_URL=$(terraform output -raw service_url)

echo -e "\n========================================================================"
echo "🎉 Phase 3 Successful! Your Steampunk Dashboard is live!"
echo "👉 Dashboard URL: $SERVICE_URL"
echo "========================================================================"
