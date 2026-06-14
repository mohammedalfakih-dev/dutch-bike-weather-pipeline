# Week 7 Project: Dutch Bike Weather Pipeline

## What it does

This pipeline fetches one day of hourly weather forecasts from the Open-Meteo API for five Dutch cities: Amsterdam, Rotterdam, Utrecht, Den Haag, and Eindhoven.

It validates the API data with Pydantic, transforms it with pandas into bike-friendly weather advice, stores the cleaned rows in Azure Postgres, and uploads the raw JSON data to Azure Blob Storage.

## Architecture

```text
Open-Meteo API ──► pipeline.py ──► Pydantic validation ──► pandas transformations
                                                                  │
                                                                  ├──► Postgres INSERT/UPDATE
                                                                  │    dev_mohammedalfakih_dev.bike_weather_forecasts
                                                                  │
                                                                  └──► Blob Storage raw JSON
                                                                       raw/bike-weather/
```

## Run locally

```bash
# 1. Populate .env from Azure Key Vault
cp .env.example .env
echo "POSTGRES_URL=$(az keyvault secret show --vault-name kv-hyf-data --name postgres-url --query value -o tsv)" >> .env
echo "AZURE_STORAGE_CONNECTION_STRING=$(az keyvault secret show --vault-name kv-hyf-data --name storage-connection-string --query value -o tsv)" >> .env
# Set your personal schema:
echo "DB_SCHEMA=dev_mohammedalfakih_dev" >> .env
echo "LOG_LEVEL=INFO" >> .env

# 2. Install dependencies
uv sync

# 3. Run directly (without Docker)
uv run python -m src.pipeline

# 4. Or build and run with Docker
docker build -t dutch-bike-weather-pipeline:v1 .
docker run --env-file .env dutch-bike-weather-pipeline:v1
```

The pipeline should fetch 120 records per run: 5 cities × 24 hourly forecasts.

## Run tests

```bash
uv run ruff check src/
uv run ruff format --check src/
uv run pytest tests/ -v
```

## Deploy to Azure

The GitHub Actions workflow builds and pushes the Docker image to Azure Container Registry after changes are merged into `main`.

The image is tagged with the GitHub commit SHA:

```text
hyfregistry.azurecr.io/dutch-bike-weather-pipeline:<commit-sha>
```

Use the SHA tag from the successful GitHub Actions run when creating or updating the Container App Job.

```bash
IMAGE_TAG="<commit-sha-from-github-actions>"
IMAGE="hyfregistry.azurecr.io/dutch-bike-weather-pipeline:${IMAGE_TAG}"

# Create Container App Job (runs daily at 06:00 UTC)
az containerapp job create \
  --name mohammedalfakih-bike-weather-job \
  --resource-group rg-hyf-data \
  --environment env-hyf-data \
  --image "$IMAGE" \
  --registry-server hyfregistry.azurecr.io \
  --trigger-type Schedule \
  --cron-expression "0 6 * * *" \
  --replica-timeout 300 \
  --replica-retry-limit 0 \
  --env-vars \
    POSTGRES_URL="$(az keyvault secret show --vault-name kv-hyf-data --name postgres-url --query value -o tsv)" \
    AZURE_STORAGE_CONNECTION_STRING="$(az keyvault secret show --vault-name kv-hyf-data --name storage-connection-string --query value -o tsv)" \
    DB_SCHEMA=dev_mohammedalfakih_dev \
    LOG_LEVEL=INFO

# Trigger a manual run for testing (without waiting for the schedule)
az containerapp job start \
  --name mohammedalfakih-bike-weather-job \
  --resource-group rg-hyf-data
```

## Enable ACR push from CI (optional)

ACR push is enabled in `.github/workflows/ci.yml`.

To allow GitHub Actions to log in to Azure, add this repository secret in **Settings → Secrets and variables → Actions**:

| Secret name         | Value                                                                                          |
| ------------------- | ---------------------------------------------------------------------------------------------- |
| `AZURE_CREDENTIALS` | Azure service principal JSON with `clientId`, `clientSecret`, `tenantId`, and `subscriptionId` |

The workflow behavior is:

- Pull requests run linting, formatting, and tests.
- Pushes to `main` run linting, formatting, tests, then build and push the Docker image to ACR.
- Images are pushed with the commit SHA only, not `latest`.

Example image:

```text
hyfregistry.azurecr.io/dutch-bike-weather-pipeline:<commit-sha>
```

## Install psql

`psql` is the Postgres command-line client used to verify results. Install it once:

**macOS**

```bash
brew install libpq
echo 'export PATH="/opt/homebrew/opt/libpq/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Linux (Debian/Ubuntu)**

```bash
sudo apt-get install -y postgresql-client
```

**Windows**
Download and run the installer from [postgresql.org/download/windows](https://www.postgresql.org/download/windows/). The installer includes `psql`.

After installing, open a new terminal and verify with:

```bash
psql --version

```

## Verify results

```bash
# Check job execution
az containerapp job execution list \
  --name mohammedalfakih-bike-weather-job \
  --resource-group rg-hyf-data \
  --output table

# Check Postgres
psql "$POSTGRES_URL" -c "SELECT COUNT(*) FROM dev_mohammedalfakih_dev.bike_weather_forecasts;"

# Check recent rows
psql "$POSTGRES_URL" -c "SELECT city, forecast_time, bike_score, bike_advice FROM dev_mohammedalfakih_dev.bike_weather_forecasts ORDER BY ingested_at DESC LIMIT 10;"

# Check Blob Storage
AZURE_STORAGE_CONNECTION_STRING="$(az keyvault secret show --vault-name kv-hyf-data --name storage-connection-string --query value -o tsv)"

az storage blob list \
  --container-name raw \
  --prefix bike-weather/ \
  --connection-string "$AZURE_STORAGE_CONNECTION_STRING" \
  --output table
```

## Clean up

```bash
az containerapp job delete \
  --name mohammedalfakih-bike-weather-job \
  --resource-group rg-hyf-data \
  --yes
```
