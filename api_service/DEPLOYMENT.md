# Deployment Guide

This guide explains how to deploy the SelfHydro API service to Google Cloud Platform using Cloud Run.

## Prerequisites

1. Google Cloud SDK installed
2. Docker installed
3. Google Cloud project created
4. Required APIs enabled:
   - Cloud Run API
   - Cloud Build API
   - Container Registry API
   - Cloud Storage API

## Initial Setup

1. Set up Google Cloud project:
   ```bash
   # Set your project ID
   export PROJECT_ID=your-project-id
   gcloud config set project $PROJECT_ID
   
   # Enable required APIs
   gcloud services enable \
     run.googleapis.com \
     cloudbuild.googleapis.com \
     containerregistry.googleapis.com \
     storage.googleapis.com
   ```

2. Create a service account for the API:
   ```bash
   # Create service account
   gcloud iam service-accounts create selfhydro-api \
     --display-name="SelfHydro API Service Account"
   
   # Grant necessary permissions
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:selfhydro-api@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/storage.objectViewer"
   ```

## Manual Deployment

1. Build the container:
   ```bash
   docker build -t gcr.io/$PROJECT_ID/selfhydro-api .
   ```

2. Push to Container Registry:
   ```bash
   docker push gcr.io/$PROJECT_ID/selfhydro-api
   ```

3. Deploy to Cloud Run:
   ```bash
   gcloud run deploy selfhydro-api \
     --image gcr.io/$PROJECT_ID/selfhydro-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="GCS_BUCKET=your-bucket,BASE_URL=https://your-domain.com,SENSOR_URL=http://sensor-service-url"
   ```

## Automated Deployment with Cloud Build

1. Create a Cloud Build trigger:
   ```bash
   gcloud beta builds triggers create github \
     --repo-name=your-repo-name \
     --repo-owner=your-github-username \
     --branch-pattern="^main$" \
     --build-config=api_service/cloudbuild.yaml
   ```

2. Set up substitution variables in the Cloud Build trigger:
   - `_GCS_BUCKET`: Your Google Cloud Storage bucket name
   - `_BASE_URL`: Your base URL for serving images
   - `_SENSOR_URL`: URL of your sensor service
   - `_REGION`: Deployment region (defaults to us-central1)

3. Push to the main branch to trigger deployment.

## Environment Variables

The service requires the following environment variables:

- `GCS_BUCKET`: Name of the Google Cloud Storage bucket
- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `BASE_URL`: Base URL for serving images
- `SENSOR_URL`: URL of the Rust sensor service
- `PORT`: Port to run the service on (default: 8000)
- `ENV`: Environment name (development/production)

## Monitoring

1. View logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=selfhydro-api"
   ```

2. Monitor service:
   ```bash
   gcloud run services describe selfhydro-api
   ```

## Troubleshooting

1. If deployment fails:
   - Check Cloud Build logs
   - Verify service account permissions
   - Check environment variables are set correctly

2. If runtime errors occur:
   - Check Cloud Run logs
   - Verify connectivity to GCS and sensor service
   - Check environment variables in Cloud Run configuration

3. If image serving fails:
   - Verify GCS bucket permissions
   - Check BASE_URL configuration
   - Verify image paths in GCS 