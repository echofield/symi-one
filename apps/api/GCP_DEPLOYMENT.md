# SYMIONE Pay API - Google Cloud Deployment Guide

**Project ID:** `symione-491117`
**Region:** `europe-west1`
**Service:** `symione-api`

---

## Prerequisites

1. Google Cloud SDK (`gcloud`) installed: https://cloud.google.com/sdk/docs/install
2. Docker installed (for local builds) OR use Cloud Build
3. Authenticated: `gcloud auth login`

---

## Step 1: Set Up Google Cloud Project

```bash
# Set project
gcloud config set project symione-491117

# Set default region
gcloud config set run/region europe-west1
```

---

## Step 2: Enable Required APIs

Copy and paste this entire block:

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com \
  cloudbuild.googleapis.com \
  compute.googleapis.com
```

---

## Step 3: Create Artifact Registry Repository

```bash
gcloud artifacts repositories create symione-repo \
  --repository-format=docker \
  --location=europe-west1 \
  --description="SYMIONE Pay container images"
```

Configure Docker to use the registry:

```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
```

---

## Step 4: Create Cloud SQL PostgreSQL Instance

### 4a. Create the instance (this takes ~5 minutes)

```bash
gcloud sql instances create symione-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=europe-west1 \
  --storage-type=SSD \
  --storage-size=10GB \
  --availability-type=zonal
```

**Note:** `db-f1-micro` is the cheapest tier (~$7/month). For production, consider `db-g1-small` or higher.

### 4b. Set the postgres password

**YOU MUST SAVE THIS PASSWORD** - paste it only once here:

```bash
gcloud sql users set-password postgres \
  --instance=symione-db \
  --password=YOUR_STRONG_PASSWORD_HERE
```

**Password requirements:**
- Use **alphanumeric characters only** (A-Z, a-z, 0-9) to avoid URL-encoding issues
- If your password contains `@`, `#`, `%`, `+`, `/`, or other special chars, you must URL-encode it in `DATABASE_URL` (e.g., `@` becomes `%40`)
- Safest for v1: stick to alphanumeric

**Generate a safe password:**
```bash
# Alphanumeric only (recommended):
openssl rand -hex 24

# Or base64 (may need URL-encoding):
openssl rand -base64 32
```

### 4c. Create the database

```bash
gcloud sql databases create symione_pay \
  --instance=symione-db
```

### 4d. Get the connection name (you'll need this)

```bash
gcloud sql instances describe symione-db --format="value(connectionName)"
```

**Expected output:** `symione-491117:europe-west1:symione-db`

---

## Step 5: Create Secrets in Secret Manager

### 5a. Create the DATABASE_URL secret

The format for Cloud Run + Cloud SQL with Unix socket:

```
postgresql+asyncpg://postgres:YOUR_PASSWORD@/symione_pay?host=/cloudsql/symione-491117:europe-west1:symione-db
```

Create the secret (replace `YOUR_PASSWORD` with your actual password):

```bash
echo -n "postgresql+asyncpg://postgres:YOUR_PASSWORD@/symione_pay?host=/cloudsql/symione-491117:europe-west1:symione-db" | \
  gcloud secrets create DATABASE_URL --data-file=-
```

### 5b. Create other secrets

**SECRET_KEY** (auto-generate):
```bash
openssl rand -base64 32 | gcloud secrets create SECRET_KEY --data-file=-
```

**STRIPE_SECRET_KEY** (paste your Stripe test key):
```bash
echo -n "sk_test_YOUR_STRIPE_KEY" | gcloud secrets create STRIPE_SECRET_KEY --data-file=-
```

**STRIPE_WEBHOOK_SECRET** (you'll get this after registering the webhook in Stripe):
```bash
echo -n "whsec_YOUR_WEBHOOK_SECRET" | gcloud secrets create STRIPE_WEBHOOK_SECRET --data-file=-
```

**ANTHROPIC_API_KEY** (paste your Anthropic key):
```bash
echo -n "sk-ant-YOUR_ANTHROPIC_KEY" | gcloud secrets create ANTHROPIC_API_KEY --data-file=-
```

**ADMIN_BOOTSTRAP_TOKEN** (for initial API key creation):
```bash
openssl rand -base64 32 | gcloud secrets create ADMIN_BOOTSTRAP_TOKEN --data-file=-
```

---

## Step 6: Build and Push Docker Image

Navigate to the API directory:

```bash
cd apps/api
```

### Option A: Build with Cloud Build (recommended - no local Docker needed)

```bash
gcloud builds submit --tag europe-west1-docker.pkg.dev/symione-491117/symione-repo/symione-api:latest
```

### Option B: Build locally and push

```bash
# Build
docker build -t europe-west1-docker.pkg.dev/symione-491117/symione-repo/symione-api:latest .

# Push
docker push europe-west1-docker.pkg.dev/symione-491117/symione-repo/symione-api:latest
```

---

## Step 7: Create Cloud Run Service Account

```bash
# Create service account
gcloud iam service-accounts create symione-api-sa \
  --display-name="SYMIONE API Service Account"

# Grant Secret Manager access
gcloud projects add-iam-policy-binding symione-491117 \
  --member="serviceAccount:symione-api-sa@symione-491117.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Grant Cloud SQL Client access
gcloud projects add-iam-policy-binding symione-491117 \
  --member="serviceAccount:symione-api-sa@symione-491117.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

---

## Step 8: Deploy to Cloud Run

```bash
gcloud run deploy symione-api \
  --image=europe-west1-docker.pkg.dev/symione-491117/symione-repo/symione-api:latest \
  --region=europe-west1 \
  --platform=managed \
  --port=8080 \
  --service-account=symione-api-sa@symione-491117.iam.gserviceaccount.com \
  --add-cloudsql-instances=symione-491117:europe-west1:symione-db \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest,STRIPE_SECRET_KEY=STRIPE_SECRET_KEY:latest,STRIPE_WEBHOOK_SECRET=STRIPE_WEBHOOK_SECRET:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,ADMIN_BOOTSTRAP_TOKEN=ADMIN_BOOTSTRAP_TOKEN:latest \
  --set-env-vars=APP_ENV=production,CORS_ORIGINS="https://symione.dev,https://app.symione.dev" \
  --min-instances=0 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --allow-unauthenticated
```

**Note:** Some `gcloud` versions require comma-separated secrets in a single `--set-secrets` flag (shown above). If you get errors, check `gcloud --version` and update if needed.

**Tradeoff on `--min-instances`:**
- `0`: Cheaper (scales to zero), but first request after idle may take 2-5 seconds (cold start)
- `1`: Always warm, instant responses, but costs ~$15-25/month extra

For Stripe webhooks, `0` is usually fine - Stripe retries failed webhooks.

---

## Step 9: Get the Cloud Run URL

```bash
gcloud run services describe symione-api --region=europe-west1 --format="value(status.url)"
```

**Expected output:** `https://symione-api-XXXXXX-ew.a.run.app`

**Save this URL** - you'll need it for:
- Stripe webhook configuration
- Setting `PUBLIC_URL` env var (optional)

---

## Step 10: Run Database Migrations

**IMPORTANT:** Run migrations immediately after deploying the service (Step 8). Until migrations complete, API endpoints that touch the database will return 500 errors. This is a short window, but don't consider the system "live" until migrations succeed.

### Option A: Cloud Run Job (recommended)

Create a one-time migration job:

```bash
gcloud run jobs create symione-migrate \
  --image=europe-west1-docker.pkg.dev/symione-491117/symione-repo/symione-api:latest \
  --region=europe-west1 \
  --service-account=symione-api-sa@symione-491117.iam.gserviceaccount.com \
  --add-cloudsql-instances=symione-491117:europe-west1:symione-db \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest \
  --command=alembic \
  --args=upgrade,head \
  --max-retries=0 \
  --task-timeout=300
```

Run the migration:

```bash
gcloud run jobs execute symione-migrate --region=europe-west1 --wait
```

### Option B: Cloud Shell with SQL Auth Proxy

Open Cloud Shell: https://console.cloud.google.com/cloudshell

```bash
# Start the proxy
cloud_sql_proxy -instances=symione-491117:europe-west1:symione-db=tcp:5432 &

# Wait a few seconds, then set the URL
export DATABASE_URL="postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/symione_pay"

# Clone repo and run migrations
git clone YOUR_REPO_URL
cd symione-pay/apps/api
pip install -r requirements.txt
alembic upgrade head
```

---

## Step 11: Verify Deployment

### Health check:

```bash
curl https://YOUR_CLOUD_RUN_URL/health
```

**Expected response:**
```json
{"status": "ok", "service": "symione-pay-api"}
```

### Check logs:

```bash
gcloud run services logs read symione-api --region=europe-west1 --limit=50
```

---

## Step 12: Configure Stripe Webhook

1. Go to **Stripe Dashboard** > **Developers** > **Webhooks**
2. Click **Add endpoint**
3. **Endpoint URL:** `https://YOUR_CLOUD_RUN_URL/api/stripe/webhook`
4. **Events to listen for:** Select these events (the ones the API actually handles):
   - `payment_intent.succeeded` (required - triggers funding confirmation)
   - `payment_intent.payment_failed` (optional - logged)
   - `payment_intent.canceled` (optional - logged)
5. Click **Add endpoint**
6. **Copy the signing secret** (starts with `whsec_`)
7. Update the secret in GCP:

```bash
echo -n "whsec_YOUR_NEW_SECRET" | gcloud secrets versions add STRIPE_WEBHOOK_SECRET --data-file=-
```

8. Redeploy to pick up the new secret (or wait for next deploy):

```bash
gcloud run services update symione-api --region=europe-west1
```

---

## Quick Reference: Redeploy After Code Changes

```bash
# From apps/api directory:
gcloud builds submit --tag europe-west1-docker.pkg.dev/symione-491117/symione-repo/symione-api:latest

# Deploy new image:
gcloud run deploy symione-api \
  --image=europe-west1-docker.pkg.dev/symione-491117/symione-repo/symione-api:latest \
  --region=europe-west1
```

---

## Costs Estimate (europe-west1)

| Resource | Monthly Cost |
|----------|--------------|
| Cloud SQL (db-f1-micro) | ~$7 |
| Cloud Run (min-instances=0, moderate traffic) | ~$5-15 |
| Artifact Registry | ~$1 |
| Secret Manager | ~$0.50 |
| **Total** | **~$15-25/month** |

---

## Troubleshooting

### "Connection refused" to database

- Verify `--add-cloudsql-instances` is set correctly
- Check service account has `roles/cloudsql.client`
- Verify DATABASE_URL uses Unix socket path: `?host=/cloudsql/PROJECT:REGION:INSTANCE`

### Migrations fail

- Ensure the DATABASE_URL strips `+asyncpg` for alembic (the env.py already handles this)
- Check Cloud Run Job logs: `gcloud run jobs executions logs --job=symione-migrate --region=europe-west1`
- **psycopg3 driver issue:** After stripping `+asyncpg`, you get `postgresql://...`. If migrations fail with driver errors, the app uses `psycopg[binary]` (psycopg3). Try changing `alembic/env.py` line 30 to use `postgresql+psycopg://` instead of just `postgresql://`:
  ```python
  # In get_url(), change the replace to:
  return os.getenv("DATABASE_URL", "...").replace("+asyncpg", "+psycopg")
  ```

### Cold start issues

- Set `--min-instances=1` for always-warm service
- Reduce image size by using `python:3.11-slim`

---

## Summary Checklist

- [ ] APIs enabled (run.googleapis.com, sqladmin.googleapis.com, etc.)
- [ ] Artifact Registry repository created
- [ ] Cloud SQL instance + database created
- [ ] Postgres password saved securely (alphanumeric recommended)
- [ ] All secrets created in Secret Manager
- [ ] Docker image built and pushed
- [ ] Service account created with correct permissions
- [ ] Cloud Run service deployed
- [ ] **Migrations run via Cloud Run Job** (do this immediately after deploy!)
- [ ] Health check returns 200: `curl https://URL/health`
- [ ] Stripe webhook URL registered with correct events (`payment_intent.succeeded`)
- [ ] STRIPE_WEBHOOK_SECRET updated with actual `whsec_...` value
- [ ] Test one full execution flow in Stripe test mode
