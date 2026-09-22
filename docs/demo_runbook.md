# Smart Harvest local demo runbook

This runbook demonstrates the training challenge replay and API behavior. It does not demonstrate production or live operation.

## 1. Start the backend

Prerequisites from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".\backend[test]"
```

Expected service origin: `http://localhost:8000`.

### Mode A — Analytics not configured

Start without analytics environment variables:

```powershell
Remove-Item Env:SMART_HARVEST_DATA_DIR -ErrorAction SilentlyContinue
Remove-Item Env:SMART_HARVEST_BASELINE_ARTIFACT -ErrorAction SilentlyContinue
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Verify:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
```

Expected: `status = ok`, `analytics = not_configured`. The frontend shows a neutral queue availability message and does not automatically request `/api/v1/assessments`. Explicit manual Batch ID lookup remains available and returns HTTP 503 while analytics is not configured. The synthetic `GET /api/v1/demo/assessment` route remains a separate fixture API and is not used by this workspace.

### Mode B — Configured training baseline

Set the runtime paths in the same PowerShell terminal before launching:

```powershell
$env:SMART_HARVEST_DATA_DIR = (Resolve-Path "sponsor_pack/data")
$env:SMART_HARVEST_BASELINE_ARTIFACT = (Resolve-Path "backend/artifacts/baseline-crop-median-v1-p1-s2024.json")
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Verify:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
Invoke-RestMethod http://localhost:8000/api/v1/assessments
Invoke-RestMethod http://localhost:8000/api/v1/assessments/BAT-000901
```

Expected: health reports `analytics = ready`. The collection returns HTTP 200 with `total_count = 18`, 18 items, `window_start = 2025-11-29T00:00:00+03:00`, and `window_end = 2025-12-01T00:00:00+03:00`. The API orders by severity score descending, then Batch ID ascending for ties. `BAT-000901` returns an assessed training challenge batch with `risk.score = 0.0644` and simulation notice `SIMULATION / training challenge dataset / deterministic baseline / not production deployment`. A Season-2024 training-partition batch such as `BAT-000001` returns HTTP 409; an unknown Batch ID returns HTTP 404. Assessment responses include `Cache-Control: no-store`.

## 2. Start the frontend

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to the backend. `VITE_API_BASE_URL` can override this for local integration.

With Mode B, the frontend requests health, then automatically loads the priority queue from `GET /api/v1/assessments`. It shows the effective replay window, count, engine version, Batch IDs, four-decimal predicted loss severity scores, and the returned simulation disclosure. Equal scores are ties; queue rows have no ordinal rank. No batch is initially selected. Selecting a queue row passes that collection assessment to the existing AssessmentCard without a second single-batch request. The independent single-batch lookup still sends `GET /api/v1/assessments/{batch_id}` and shows its normal 404/409/503 feedback.

Use browser Network or backend access logs to verify the request distinction: initial load sends health and collection GETs; queue selection sends no `GET /api/v1/assessments/{batch_id}`; manual lookup of `BAT-000901` sends that single-batch GET. At approximately 375 px, the page stacks queue, detail, lookup, then system status.

If the backend cannot be reached, the page shows `Unavailable` and `Try again`. If analytics is not ready, the reachable backend status remains visible and the queue is not automatically loaded. A collection request failure is shown locally in the queue with a retry control.

## Reset

Reload the page to fetch a fresh replay. No stateful reset is required.
