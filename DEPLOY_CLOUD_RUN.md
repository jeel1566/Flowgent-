# Deploy Flowgent Backend to Google Cloud Run

## Prerequisites
1. Google Cloud account with $5 credits
2. `gcloud` CLI installed: https://cloud.google.com/sdk/docs/install
3. Docker installed (optional, Cloud Build will handle it)

## Quick Deploy (5 Minutes)

### Step 1: Setup Google Cloud Project
```bash
# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create flowgent-backend --name="Flowgent Backend"

# Set the project
gcloud config set project flowgent-backend

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### Step 2: Set Environment Variables
```bash
# Navigate to backend directory
cd D:\Flowgent\backend

# Create .env.yaml for Cloud Run secrets
cat > .env.yaml << EOF
GOOGLE_GENAI_API_KEY: "your-gemini-api-key-here"
N8N_MCP_URL: "https://api.n8n-mcp.com/mcp"
N8N_MCP_API_KEY: "your-n8n-mcp-key-here"
ALLOWED_ORIGINS: "*"
EOF
```

### Step 3: Deploy to Cloud Run
```bash
# Deploy with minimal cost settings
gcloud run deploy flowgent-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 2 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300s \
  --concurrency 80 \
  --env-vars-file .env.yaml

# This will:
# - Build Docker image using Cloud Build
# - Deploy to Cloud Run
# - Give you a URL like: https://flowgent-backend-xxxxx-uc.a.run.app
```

### Step 4: Test Deployment
```bash
# Get the service URL
gcloud run services describe flowgent-backend --region us-central1 --format 'value(status.url)'

# Test health endpoint
curl https://YOUR-SERVICE-URL/health

# Test API docs
# Open in browser: https://YOUR-SERVICE-URL/docs
```

### Step 5: Update Extension
Update your Chrome extension to use the Cloud Run URL:
```javascript
// In extension/lib/config.js or similar
const API_URL = 'https://flowgent-backend-xxxxx-uc.a.run.app';
```

## Cost Optimization for $5 Credit

### Current Settings (Minimal Cost):
- **min-instances: 0** - Scales to zero when idle (FREE!)
- **max-instances: 2** - Limits max cost
- **memory: 512Mi** - Smallest practical size
- **cpu: 1** - Minimum CPU

### Expected Costs:
- **Free tier**: 2 million requests/month, 360,000 GB-seconds
- **Your $5 will give you**: ~5-10 hours of constant usage
- **With scale-to-zero**: Should last weeks for testing

### If You Need to Save More:
```bash
# Reduce memory further (may be slow)
gcloud run services update flowgent-backend \
  --memory 256Mi \
  --region us-central1

# Reduce timeout
gcloud run services update flowgent-backend \
  --timeout 60s \
  --region us-central1
```

## Monitor Costs
```bash
# Check billing
gcloud billing accounts list

# Check service metrics
gcloud run services describe flowgent-backend --region us-central1
```

## Update Deployment
```bash
# After code changes, just redeploy
cd D:\Flowgent\backend
gcloud run deploy flowgent-backend --source . --region us-central1
```

## View Logs
```bash
# Stream logs
gcloud run services logs tail flowgent-backend --region us-central1

# Or view in Cloud Console:
# https://console.cloud.google.com/run
```

## Rollback if Needed
```bash
# List revisions
gcloud run revisions list --service flowgent-backend --region us-central1

# Rollback to previous
gcloud run services update-traffic flowgent-backend \
  --to-revisions REVISION-NAME=100 \
  --region us-central1
```

## Delete to Stop Costs
```bash
# Delete the service
gcloud run services delete flowgent-backend --region us-central1

# Delete the project (removes everything)
gcloud projects delete flowgent-backend
```

## Troubleshooting

### Build Fails
- Check Dockerfile syntax
- Ensure requirements.txt has all dependencies
- View build logs in Cloud Console

### Cold Starts Too Slow
- Increase memory to 1Gi
- Set min-instances to 1 (costs ~$5/month)

### CORS Issues
- Ensure ALLOWED_ORIGINS="*" in .env.yaml
- Check extension uses HTTPS URL

### API Key Errors
- Verify .env.yaml has correct keys
- Check Cloud Run environment variables in console

## Alternative: One-Command Deploy
```bash
# If you want to skip .env.yaml and set inline
gcloud run deploy flowgent-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_API_KEY=your-key,N8N_MCP_URL=https://api.n8n-mcp.com/mcp,N8N_MCP_API_KEY=your-key,ALLOWED_ORIGINS=*
```

## Security Notes (After Testing)
- Change `--allow-unauthenticated` to require auth
- Use Secret Manager for API keys (not env vars)
- Restrict CORS to specific domains
