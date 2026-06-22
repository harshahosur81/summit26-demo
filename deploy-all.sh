#!/usr/bin/env bash
# Exit immediately if any command exits with a non-zero status
set -e

# Resolve absolute path of the repository root
REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$REPO_ROOT"

echo "========================================================================"
echo "🛡️  STARTING COMPLETE END-TO-END REPO DEPLOYMENT (SUMMIT26-DEMO)"
echo "========================================================================"

# Pre-flight check: ensure gcloud is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
  echo "❌ Error: No active gcloud account detected."
  echo "Please authenticate using: gcloud auth login"
  exit 1
fi

# 1. Execute Phase 1: Enable APIs, Create Registry, Compile & Upload App Image
"$REPO_ROOT/terraform/phase1-registry/deploy.sh"

# 2. Execute Phase 2: Create Storage Buckets, Service Accounts, and Vault Secrets
"$REPO_ROOT/terraform/phase2-infra/deploy.sh"

# 3. Execute Phase 3: Provision Cloud Run Instance with FUSE Persistence & Public Domain
"$REPO_ROOT/terraform/phase3-app/deploy.sh"

echo "========================================================================"
echo "🔥 END-TO-END DEPLOYMENT SUCCESSFUL! ALL PHASES PROVISIONED AND ONLINE!"
echo "========================================================================"
