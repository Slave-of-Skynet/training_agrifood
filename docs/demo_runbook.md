# Smart Harvest local demo runbook

This runbook provides the reproducible procedure for demonstrating the Smart Harvest decision support prototype.
This is a **SIMULATION / training challenge** demonstration on recorded sponsor data. It does not demonstrate production deployment, live commercial operations, or learned machine learning models.

---

## 1. Prerequisites and Clean Setup

Ensure the following prerequisites are installed on the presentation machine:
- **Python**: `>= 3.11` (verified with `python --version`)
- **Node.js**: `^20.19.0 || >= 22.12.0` (verified with `node --version`)
- **npm**: (verified with `npm --version`)
- **Git**: (verified with `git --version`)
- **PowerShell**: Windows-first terminal environment

### Clean setup from repository root

In a PowerShell terminal:

```powershell
# 1. Prepare Python virtual environment and backend dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".\backend[test]"

# 2. Install frontend dependencies cleanly from lockfile
cd frontend
npm ci
cd ..
```

---

## 2. Primary Demo Path — Mode B (Configured Training Baseline)

This is the **Level 1 (Primary)** demonstration path.

### Step 2.1 — Start the backend in Mode B

In Terminal 1 (from repository root):

```powershell
$env:SMART_HARVEST_DATA_DIR = (Resolve-Path "sponsor_pack/data")
$env:SMART_HARVEST_BASELINE_ARTIFACT = (Resolve-Path "backend/artifacts/baseline-crop-median-v1-p1-s2024.json")

.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Service starts on `http://127.0.0.1:8000`.

### Step 2.2 — Quick API health check

In a second terminal, verify readiness before launching the UI:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Expected output:
```json
{
  "status": "ok",
  "service": "smart-harvest",
  "analytics": "ready"
}
```

### Step 2.3 — Start the frontend dev server

In Terminal 2:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1
```

Vite dev server starts on `http://127.0.0.1:5173/` and proxies `/api` requests to `http://127.0.0.1:8000`.

### Step 2.4 — Execute the UI Demo Flow

1. **Open the browser**: Navigate to `http://127.0.0.1:5173`.
2. **Observe initial queue auto-load**:
   - Status badge (bottom/side): `Connected`, Service: `smart-harvest`, Analytics: `ready`.
   - Priority Queue automatically loads 18 held-out batches for the accepted replay window (`2025-11-29T00:00:00+03:00` to `2025-12-01T00:00:00+03:00`).
   - Notice banner: `SIMULATION / training challenge dataset / deterministic baseline / not production deployment`.
   - Batch review area initially prompts: *"Select a batch to review"*.
3. **Inspect ranking and ties**:
   - Highlight that the top items (starting with `BAT-000910`, `BAT-000950`, `BAT-001043`...) share an identical loss severity score of `0.1476`.
   - Clarify the domain invariant: these batches form an equal-risk tied cohort; Batch ID is used only for deterministic secondary ordering. There is no fake ordinal rank or arbitrary preference among ties.
4. **Demonstrate queue selection**:
   - Click **"View assessment for BAT-000910"**.
   - The Batch Assessment card populates instantly with `BAT-000910` and predicted loss severity score `0.1476`.
   - Explain that this selection reuses the assessment already returned by the collection query; no redundant network request is fired.
   - Walk through the honest bounds:
     - Deterioration timing: *Not estimable from supplied observations* (`null`).
     - Recommendation: *Action recommendations are unavailable* (`null`).
     - Factors: *None* (`[]`).
     - Score explanation: computed from historical crop medians in the training partition, clipped and scaled to `[0, 1]`.
5. **Demonstrate manual single-batch lookup**:
   - In the **Evaluate Batch** form, enter `BAT-000901` and click **Load assessment**.
   - The card updates to display `BAT-000901` with score `0.0644`.
   - Highlight that `BAT-000901` is a Season-2025 held-out batch.
   - (Optional negative check): Enter Season-2024 training batch `BAT-000001` to show release-eligibility rejection (HTTP 409: not eligible for this assessment release), or enter `BAT-999999` to show HTTP 404 (Batch not found).

---

## 3. Fallback Ladder

If any component experiences unexpected local friction during presentation, follow this strict fallback ladder:

### Level 1 — Primary (Recommended)
- Mode B backend (`127.0.0.1:8000`) + Vite development server (`127.0.0.1:5173`) with proxy.

### Level 2 — Local Production-Build Fallback (No Vite Dev Proxy)
If the Vite development proxy encounters network issues or port collisions:
1. Stop the frontend dev server.
2. Restart the backend with CORS configured for preview:
   ```powershell
   $env:SMART_HARVEST_CORS_ORIGINS = "http://127.0.0.1:4173"
   .\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
   ```
3. Build and preview the frontend against direct local API origin:
   ```powershell
   cd frontend
   $env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
   npm run build
   npm run preview -- --host 127.0.0.1 --port 4173
   ```
4. Open `http://127.0.0.1:4173`. Network requests call `http://127.0.0.1:8000/api/...` directly with verified CORS headers. All queue and lookup interactions function identically.

### Level 3 — Direct API Evidence Fallback
If the browser or frontend cannot run (e.g. display server issues):
Execute PowerShell inspection directly in terminal to prove complete backend and business logic integrity:
```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/assessments
Invoke-RestMethod http://127.0.0.1:8000/api/v1/assessments/BAT-000901
```
This serves as degraded technical proof of the working candidate.

### Level 4 — Honest Degraded / Unavailable State
If dataset loading or artifact validation fails:
- Backend reports `analytics: unavailable` or `not_configured`.
- The frontend clearly displays `Unavailable` and retry controls.
- **Rule of Integrity**: Never substitute synthetic fixtures, pre-rendered screenshots, or fabricated batch queues as if they were live dataset-backed assessments. Acknowledge the degraded condition transparently.

---

## 4. Secondary Verification Path — Mode A (Unconfigured Startup)

For verifying baseline fallback behavior when analytics variables are omitted:

```powershell
Remove-Item Env:SMART_HARVEST_DATA_DIR -ErrorAction SilentlyContinue
Remove-Item Env:SMART_HARVEST_BASELINE_ARTIFACT -ErrorAction SilentlyContinue

.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Verify:
```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```
Expected: `status = ok`, `analytics = not_configured`.
In the frontend, the service status indicates reachable backend, but the priority queue is not automatically requested. Manual batch lookups return HTTP 503 (`Analytics runtime unavailable`).

---

## 5. Reset and Teardown Procedure

To reset demo state between presentations:
- **Browser reload**: Simply reload `http://127.0.0.1:5173` in the browser. The prototype is stateless; reloading fetches a fresh snapshot without local storage pollution.
- **Process termination**: In each PowerShell terminal, press `Ctrl+C` to terminate `uvicorn` and `vite`.
- **Environment cleanup**:
  ```powershell
  Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
  Remove-Item Env:SMART_HARVEST_CORS_ORIGINS -ErrorAction SilentlyContinue
  Remove-Item Env:SMART_HARVEST_DATA_DIR -ErrorAction SilentlyContinue
  Remove-Item Env:SMART_HARVEST_BASELINE_ARTIFACT -ErrorAction SilentlyContinue
  ```
