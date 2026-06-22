# Installation & Deployment Guide

This document explains how to configure and deploy the **Tesla Solar Sync** application to any Google Cloud Platform (GCP) project.

---

## 📋 Prerequisites

Ensure you have the following installed locally and configured in your path:
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) (`gcloud`)
- [Terraform](https://developer.hashicorp.com/terraform/downloads) (>= 1.3)
- [Git](https://git-scm.com/downloads)

### Authenticate Google Cloud CLI
Before proceeding, authenticate your GCP account and set up local application default credentials:
```bash
gcloud auth login
gcloud auth application-default login
```

---

## ⚙️ Configuration

Deploying to your own GCP project requires configuring your variables.

1. **Create your configuration file:**
   Copy the provided example template to a local configuration file:
   ```bash
   cp terraform/terraform.tfvars.example terraform/terraform.tfvars
   ```

2. **Customize your variables:**
   Open `terraform/terraform.tfvars` in your editor and configure the fields:
   * **`project_id`**: Set this to your target GCP Project ID.
   * **`region`**: Select your preferred GCP region (e.g., `us-central1`).
   * **`vault_secret`**: Generate a secure 32-character AES vault key (used for DB encryption).
   * **`tesla_email`**: Keep as `user@example.com` to run in mock/simulation mode, or specify a registered Tesla Account email.

---

## 🚀 Execution

You can deploy the complete infrastructure in a single step using the orchestrator, or deploy step-by-step.

### Option A: Complete Orchestrated Deployment (Recommended)
Run the top-level deploy script. It automates all 3 phases (API enablement, container building, database creation, and Cloud Run setup):
```bash
chmod +x deploy-all.sh
./deploy-all.sh
```

### Option B: Step-by-Step Deployment
If you prefer to review or run each phase individually:

1. **Phase 1: Enable APIs & Build Container Image**
   Enables APIs, provisions the Artifact Registry, and compiles the container:
   ```bash
   cd terraform/phase1-registry
   terraform init
   ./deploy.sh
   ```

2. **Phase 2: Provision Supporting Infrastructure**
   Provisions Cloud Storage buckets, service accounts, and Vault secrets:
   ```bash
   cd ../phase2-infra
   terraform init
   ./deploy.sh
   ```

3. **Phase 3: Deploy Cloud Run Service**
   Deploys the application with persistent FUSE storage and mounts:
   ```bash
   cd ../phase3-app
   terraform init
   ./deploy.sh
   ```

Once completed, the script in Phase 3 outputs your live public **Dashboard URL**.
