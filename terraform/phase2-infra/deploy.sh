#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -e

# Resolve the absolute path of this script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "🚀 Starting Phase 2: Provisioning Core Supporting Infrastructure"
echo "========================================================================"

# 1. Run Terraform Apply for Phase 2
echo -e "\n📦 Applying Supporting Infrastructure (Storage, SA, & Secrets)..."
terraform apply -auto-approve

echo -e "\n========================================================================"
echo "🎉 Phase 2 Successful! Buckets, Service Accounts, and Secrets are live!"
echo "========================================================================"
