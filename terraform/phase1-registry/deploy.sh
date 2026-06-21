#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -e

# Resolve the absolute path of this script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "🚀 Starting Phase 1: Provisioning Artifact Registry & Building Container"
echo "========================================================================"

# 1. Run Terraform Apply for Phase 1 (APIs and Registry)
echo -e "\n📦 Step 1/3: Applying Terraform Configuration..."
terraform apply -auto-approve

# 2. Fetch the newly created Registry URL
echo -e "\n🔍 Step 2/3: Fetching Registry URL output..."
REGISTRY_URL=$(terraform output -raw registry_url)
echo "🎯 Target Registry: $REGISTRY_URL"

# 3. Submit code to Google Cloud Build using the fetched URL
echo -e "\n🏗️ Step 3/3: Submitting workspace to Google Cloud Build..."
cd ../..
PROJECT_ID=$(echo "$REGISTRY_URL" | cut -d'/' -f2)
gcloud builds submit --tag "${REGISTRY_URL}/solar-sync-app:latest" . --project="$PROJECT_ID"

echo -e "\n========================================================================"
echo "🎉 Phase 1 Automation Successful!"
echo "Registry is active & compiled container is stored in Artifact Registry!"
echo "========================================================================"
