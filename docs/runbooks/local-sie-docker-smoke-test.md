# Local SIE Docker Smoke Test Runbook

## Purpose

This runbook documents how to run the Superlinked Inference Engine locally with Docker and validate the `ai-consultancy-lab` Superlinked provider adapter.

This is a Week 1 operational proof artifact. It proves local provider-backed inference works through a typed adapter and trace-safe logging boundary.

## Scope

This runbook covers:

- starting SIE locally with Docker
- avoiding local port conflicts
- disabling telemetry for local validation
- verifying health and readiness endpoints
- running the Python smoke test
- interpreting first-run model download behavior
- stopping the local container

This runbook does not cover:

- hosted SIE access
- production SIE deployment
- Kubernetes, Helm, GKE, or EKS setup
- RAG evaluation
- customer-data testing
- production readiness

## Prerequisites

Run from Windows PowerShell.

Required:

- Docker Desktop running
- Python 3.12 virtual environment active
- repo path:

```text
C:\Users\kabom\Documents\Machine Learning\Machine Learning Workspace\ai-consultancy-lab
```

Validate Docker:

```powershell
docker --version
docker info
```

Validate repo environment:

```powershell
Set-Location "C:\Users\kabom\Documents\Machine Learning\Machine Learning Workspace\ai-consultancy-lab"
.\.venv\Scripts\Activate.ps1
python --version
python -m pytest
```

Expected:

```text
Python 3.12.x
8 passed
```

## Local SIE Configuration

For local Docker mode, `.env` should use localhost and no API key:

```text
SIE_BASE_URL=http://localhost:8081
SIE_API_KEY=
SIE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SIE_TIMEOUT_S=120
```

Why port `8081`?

Port `8080` may already be used by another local service. Mapping host `8081` to container `8080` avoids the conflict:

```text
localhost:8081 -> container:8080
```

## Start SIE Locally

Run in a dedicated PowerShell window and leave it open:

```powershell
docker run --rm `
  --name sie-local `
  -p 8081:8080 `
  -v sie-hf-cache:/app/.cache/huggingface `
  -e SIE_TELEMETRY_DISABLED=1 `
  ghcr.io/superlinked/sie-server:latest-cpu-default
```

Notes:

- `--rm` removes the container after it stops.
- `--name sie-local` gives the container a stable name.
- `-p 8081:8080` exposes SIE on `localhost:8081`.
- `-v sie-hf-cache:/app/.cache/huggingface` keeps model downloads cached.
- `SIE_TELEMETRY_DISABLED=1` disables anonymous telemetry during local validation.

## Verify SIE Health

In a second PowerShell window:

```powershell
curl.exe http://localhost:8081/healthz
curl.exe http://localhost:8081/readyz
```

Expected:

```text
ok
ok
```

Interpretation:

```text
/healthz ok = SIE server process is alive.
/readyz ok = SIE API server is ready to receive requests.
```

## Run the Smoke Test

From the repo root:

```powershell
Set-Location "C:\Users\kabom\Documents\Machine Learning\Machine Learning Workspace\ai-consultancy-lab"
.\.venv\Scripts\Activate.ps1

python scripts\smoke_superlinked.py
```

Expected output shape:

```json
{
  "event_name": "superlinked_encode_smoke_test_passed",
  "payload": {
    "dense_dimensions": 384,
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "output_types": ["dense"]
  },
  "provider": "superlinked",
  "timestamp": "...",
  "trace_id": "..."
}
```

The important evidence fields are:

```text
event_name = superlinked_encode_smoke_test_passed
provider = superlinked
model = sentence-transformers/all-MiniLM-L6-v2
dense_dimensions = 384
trace_id exists
```

## First-Run 503 Behavior

On first use, SIE may return temporary `503 Service Unavailable` responses while the requested model downloads and loads.

Example logs:

```text
Downloading sentence-transformers/all-MiniLM-L6-v2 from HuggingFace Hub
Fetching 15 files: 7%
POST /v1/encode/sentence-transformers/all-MiniLM-L6-v2 HTTP/1.1 503 Service Unavailable
```

This is not necessarily a failure.

Healthy progression:

```text
Fetching 15 files: 100%
Model deserialize start
Model warmup start
Model warmup end
Model loaded successfully
Background model load completed
```

After this, rerun the smoke test once.

## Troubleshooting

### Docker CLI works but Docker engine is not running

Symptom:

```text
error during connect: dockerDesktopLinuxEngine ... The system cannot find the file specified
```

Fix:

```text
Open Docker Desktop and wait until the engine is running.
```

Then rerun:

```powershell
docker info
```

### Port 8080 is already allocated

Symptom:

```text
Bind for 0.0.0.0:8080 failed: port is already allocated
```

Fix:

Use host port `8081`:

```powershell
-p 8081:8080
```

Then set:

```text
SIE_BASE_URL=http://localhost:8081
```

### Health is ok but encode returns 503

Interpretation:

```text
SIE server is alive, but the specific model is still downloading or loading.
```

Fix:

Wait for the Docker logs to show:

```text
Model 'sentence-transformers/all-MiniLM-L6-v2' loaded successfully
```

Then rerun:

```powershell
python scripts\smoke_superlinked.py
```

### Check container logs

```powershell
docker logs sie-local --tail 120
```

Follow logs live:

```powershell
docker logs sie-local --follow
```

### Check container resources

```powershell
docker stats --no-stream sie-local
```

## Stop SIE

When done testing:

```powershell
docker stop sie-local
```

The container stops, but the Hugging Face model cache remains in the Docker volume:

```text
sie-hf-cache
```

## Security and Privacy Notes

Local validation rules:

- Do not commit `.env`.
- Do not log API keys.
- Do not log raw prompts, raw customer documents, or sensitive payloads.
- Use trace IDs and metadata-safe logs.
- Keep telemetry disabled during local proof validation.
- Treat local model calls as synthetic-data validation only.

## Current Maturity Label

```text
production-shaped provider integration scaffold,
locally live-provider validated through Docker SIE,
not RAG-ready,
not customer-data tested,
not production-ready
```
