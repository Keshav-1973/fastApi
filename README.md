# FastAPI + MongoDB Project

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure environment

Create a `.env` file in the project root:

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=fastapi_db

SECRET_KEY=change_me_to_a_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

If you use MongoDB Atlas, set `MONGODB_URL` to your Atlas connection string.

## 3. Run server

```bash
uvicorn app.main:app --reload
```

## 4. Swagger docs

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0. 1:8000/redoc`

## 5. Available auth routes

- `POST /auth/register`
- `POST /auth/login`
- `GET /users/me`
- `GET /users/{user_id}`

## 6. Deploy to Google Cloud Run

The repo includes a `Dockerfile` and `.dockerignore` for Cloud Run.

### Live deployment

- Project: `fastapi-carlist-29690`
- Region: `asia-south1` (Mumbai)
- Service: `fastapi-app`
- API: https://fastapi-app-746496873789.asia-south1.run.app
- Swagger: https://fastapi-app-746496873789.asia-south1.run.app/docs

### One-time setup

```bash
# Install gcloud CLI
brew install --cask google-cloud-sdk

# Login + select project
gcloud auth login
gcloud config set project fastapi-carlist-29690

# Enable required APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

### Deploy / redeploy

Build the image in Cloud Build and deploy from source:

```bash
gcloud run deploy fastapi-app \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --env-vars-file env.yaml
```

`env.yaml` example (do **not** commit real secrets):

```yaml
MONGODB_URL: "mongodb+srv://USER:PASS@cluster.mongodb.net/"
MONGODB_DB_NAME: "fastapi_db"
SECRET_KEY: "long-random-secret"
ALGORITHM: "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: "60"
```

### Common operations

```bash
# Tail logs
gcloud run services logs tail fastapi-app --region asia-south1

# Update a single env var
gcloud run services update fastapi-app --region asia-south1 \
  --update-env-vars SECRET_KEY="$(openssl rand -hex 32)"

# Move secrets to Secret Manager (recommended for prod)
echo -n "mongodb+srv://..." | gcloud secrets create MONGODB_URL --data-file=-
gcloud run services update fastapi-app --region asia-south1 \
  --update-secrets=MONGODB_URL=MONGODB_URL:latest

# Delete the service
gcloud run services delete fastapi-app --region asia-south1
```

### Production checklist

- Replace `SECRET_KEY` with a strong random value (`openssl rand -hex 32`).
- Restrict `allow_origins` in `app/main.py` to your real frontend origin.
- In MongoDB Atlas, allow `0.0.0.0/0` (Cloud Run egress IPs are dynamic) or configure a VPC connector with a static egress IP.
- Move secrets from env vars to Secret Manager.
