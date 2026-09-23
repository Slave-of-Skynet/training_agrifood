# VLD-04A — Operational Readiness & Demo Documentation

- **Date:** 2026-09-23
- **Owner / Integrator:** Vladimir
- **Repository:** `Slave-of-Skynet/training_agrifood`
- **Task Slice:** VLD-04A (Operational readiness & demo documentation; slice of parent task VLD-04)
- **Parent Gate Status:** **BLOCKED: MISSING EVIDENCE** (only remaining blocker: independent teammate reproduction)
- **VLD-04A Slice Status:** **EVIDENCE RECORDED / READY FOR HUMAN REPOSITORY GATE**

---

## 1. Base and Purpose

### Historical Execution Base vs. PR Target
- **Executed VLD-04 evidence base:** `4363e372633eaeb09b9708c31923701852873455` (Merge PR #53 — VLD-03 End-to-End Integration & Behaviour Gate).
- **Target `main` for PR:** `a177c20dad4ed74be2dd5f46120ecc73767b8dcf` (PR #54 — VLD-05A Pre-Final Claim & Evidence Audit).
  - Note: PR #54 was documentation-only (`docs/recon/VLD-05A-claim-evidence-audit.md`), introducing no application code or operational changes. The operational evidence recorded below reflects its actual execution base at `4363e372...` without retroactive rewrite.
- **Working branch:** `vladimir/vld-04-runtime-demo-readiness`.

### Purpose
Prove that the Human Integrated Smart Harvest candidate can be:
1. Obtained directly from committed repository state;
2. Installed cleanly from documented prerequisites;
3. Verified via the standard verification gate (`scripts/verify.ps1`);
4. Started in configured Mode B with dataset-backed analytics;
5. Recovered through legitimate local fallback paths (production-build preview and direct API evidence);
6. Operated without hidden or machine-specific state;
7. Presented truthfully without false claims of remote production deployment or learned models;
8. Bounded by an accepted operational demo decision (**VLD04-D1: Option A — Local-first authoritative demo**).

Independent teammate reproduction is intentionally decoupled from this documentation PR and deferred to **VLD-04B — Independent Reproduction Closure**.

---

## 2. Runtime / Toolchain Inventory

### Toolchain Versions (Inspected on Windows Execution Host)
| Tool | Actual Version | Requirement | Status |
| --- | --- | --- | --- |
| **Python** | `Python 3.11.9` | `>= 3.11` | PASS |
| **pip** | `26.2.1` (clean venv) / `24.0` (host) | Standard pip packaging | PASS |
| **Node.js** | `v22.23.1` | `^20.19.0 \|\| >= 22.12.0` | PASS |
| **npm** | `10.9.8` | Standard npm | PASS |
| **Git** | `git version 2.54.0.windows.1` | Standard Git | PASS |
| **OS** | Windows 11 (`Windows_NT x64 10.0.26100`) | Windows-first team standard | PASS |

### Committed Runtime Resources & Settings
- **Backend:** Python / FastAPI (`backend/app/main.py`).
  - Pinned sponsor dataset snapshot: `sponsor_pack/data/` (7 CSV tables).
  - Versioned deterministic baseline artifact: `backend/artifacts/baseline-crop-median-v1-p1-s2024.json`.
  - Required process environment variables: `SMART_HARVEST_DATA_DIR`, `SMART_HARVEST_BASELINE_ARTIFACT`.
  - Optional CORS configuration: `SMART_HARVEST_CORS_ORIGINS` (defaults to `http://localhost:5173`).
- **Frontend:** React 18.3 + TypeScript + Vite 8.3 (`frontend/`).
  - Clean install: `npm ci`.
  - Development proxy: `frontend/vite.config.ts` proxies `/api` requests to `http://localhost:8000`.
  - Direct API origin override: `VITE_API_BASE_URL` (optional; empty uses same-origin / proxy).
- **Verification Helper:** `scripts/verify.ps1` runs backend pytest followed by frontend production build (`tsc -b && vite build`).
- **CI Configuration:** `.github/workflows/ci.yml` defines Python 3.11 backend tests and Node 22 frontend `npm ci` + build jobs.

---

## 3. Clean-State Installation Evidence

Clean reproducibility was executed inside an isolated, detached worktree:
- **Location:** `$clean = "$env:TEMP\training_agrifood-vld04-clean"`
- **Base commit:** `4363e372633eaeb09b9708c31923701852873455` (detached HEAD, clean working tree).

### Backend Virtual Environment & Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".\backend[test]"
```
- **Exit code:** 0.
- **Outcome:** Pip upgraded to 26.2.1. Successfully installed `smart-harvest-backend-0.1.0` in editable mode, along with `fastapi-0.141.1`, `pydantic-2.13.5`, `uvicorn-0.53.0`, `httpx-0.28.1`, `pytest-8.4.2`, and their dependencies. No dependency resolution conflicts occurred.

### Frontend Clean Installation
```powershell
cd frontend
npm ci
cd ..
```
- **Exit code:** 0.
- **Outcome:** `added 26 packages, and audited 27 packages in 3s; 0 vulnerabilities`. Verified reproducible clean install via lockfile.

---

## 4. Verification Evidence

From the clean worktree root, the committed verification helper was executed:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```
- **Exit code:** 0.
- **Backend pytest metrics:** **114 passed, 0 failed, 2 warnings in 24.28s**.
  - Warnings: `StarletteDeprecationWarning` regarding TestClient/httpx and `DeprecationWarning` regarding AnyIO BlockingPortal alias.
- **Frontend build metrics:** `tsc -b && vite build` completed in 563ms; 20 modules transformed into production assets (`dist/index.html`, `dist/assets/index-DEvRVfOT.css`, and `dist/assets/index-uOuYnRBq.js`).

---

## 5. Mode B Runtime Evidence

### Startup
Launched in clean worktree with configured process environment variables:
```powershell
$env:SMART_HARVEST_DATA_DIR = (Resolve-Path "sponsor_pack/data")
$env:SMART_HARVEST_BASELINE_ARTIFACT = (Resolve-Path "backend/artifacts/baseline-crop-median-v1-p1-s2024.json")
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```
- Lifespan validated raw CSV snapshot and baseline artifact; analytics transitioned to `ready`.

### API Smoke Responses
| Endpoint | Actual Response | Verification Details |
| --- | --- | --- |
| `GET /api/v1/health` | `HTTP 200` | `{"status":"ok","service":"smart-harvest","analytics":"ready"}` |
| `GET /api/v1/assessments` | `HTTP 200` | `total_count: 18`, 18 items returned; window `2025-11-29T00:00:00+03:00` to `2025-12-01T00:00:00+03:00`; engine `baseline-crop-median-v1-p1-s2024`. Top items form a tied cohort at score `0.1476` (e.g. `BAT-000910`, `BAT-000950`, `BAT-001043`). |
| `GET /api/v1/assessments/BAT-000901` | `HTTP 200` | `status: assessed`, `risk.score: 0.0644`, `deterioration_horizon: null`, `factors: []`, `recommendation: null`, `provenance.simulation: true`, notice present. |

---

## 6. Browser / Local Demo Evidence

### Frontend Dev Server Execution
In clean worktree `frontend/`:
```powershell
npm run dev -- --host 127.0.0.1
```
- Started Vite dev server on `http://127.0.0.1:5173/`.
- Inspected live in browser via Chrome DevTools CDP session:
  - **Status & Queue auto-load:** BackendStatus badge showed `Connected` and Analytics `ready`. Priority Queue auto-loaded 18 batches with replay bounds `2025-11-29T00:00:00+03:00` to `2025-12-01T00:00:00+03:00` and simulation notice visible.
  - **Ties display:** Top rows displayed `0.1476` with explanatory text clarifying that equal scores are ties and no fake ordinal rank is assigned.
  - **Queue selection:** Clicking `View assessment for BAT-000910` rendered detail card with score `0.1476` immediately; network logs confirmed zero duplicate single-batch network requests (reused collection assessment).
  - **Manual lookup:** Submitting `BAT-000901` in the Evaluate Batch form fetched `BAT-000901` and rendered score `0.0644`.

---

## 7. Production-Build Fallback

Verified without altering any source code:
1. Stopped Vite development server.
2. Started backend with CORS configured for preview:
   ```powershell
   $env:SMART_HARVEST_CORS_ORIGINS = "http://127.0.0.1:4173"
   .\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
   ```
3. Built frontend with direct API base URL:
   ```powershell
   cd frontend
   $env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
   npm run build
   ```
   Built in 231ms with 20 modules transformed into `dist/`.
4. Started preview server:
   ```powershell
   npm run preview -- --host 127.0.0.1 --port 4173
   ```
5. Verified on `http://127.0.0.1:4173`:
   - Connected, Analytics ready.
   - 18 batches loaded in priority queue.
   - Queue selection clicked `BAT-000910`: card populated with score `0.1476`.
   - Manual lookup submitted `BAT-000901`: card populated with score `0.0644`.
   - Backend access logs confirmed direct cross-origin HTTP calls (`GET /api/v1/health`, `GET /api/v1/assessments`, `GET /api/v1/assessments/BAT-000901`) from port 4173 without Vite proxy.
6. Cleaned up fallback environment variables and removed `$clean`.

---

## 8. Network / Offline Boundary

We distinguish two separate operational boundaries:

### A. Post-Installation Runtime Boundary (100% Offline)
- Once `.venv` and `frontend/node_modules` are installed, **the entire Smart Harvest runtime operates completely offline**.
- The backend reads exclusively from committed local files (`sponsor_pack/data/` and `backend/artifacts/`).
- The frontend connects exclusively to local backend endpoints (`127.0.0.1:8000`).
- No external CDNs, fonts, telemetry, external database connections, or cloud APIs are queried at runtime.

### B. Clean Installation Boundary (Online Dependency Resolution)
- A completely fresh clean machine requires internet access during initial setup to download:
  - Python wheels from PyPI (`pip install -e ".\backend[test]"`);
  - Node packages from npm registry (`npm ci`).
- Fully offline clean installation is not claimed unless wheels and npm tarballs are pre-cached.

### Hackathon Presentation Operational Recommendations
Before the live pitch session, the presenter laptop should:
1. Have the repository pre-cloned on the authoritative branch;
2. Have `.venv` created and dependencies pre-installed;
3. Have `frontend/node_modules` pre-installed (`npm ci`);
4. Have completed one verified local Mode B run;
5. Be connected to reliable power with browser open to `http://127.0.0.1:5173`.

---

## 9. Demo Fallback Ladder

A four-level operational fallback hierarchy is documented in [`docs/demo_runbook.md`](../demo_runbook.md):

| Level | Name | Configuration | Use When |
| --- | --- | --- | --- |
| **Level 1** | **Primary Demo** | Mode B backend (`127.0.0.1:8000`) + Vite dev server (`127.0.0.1:5173`) with dev proxy. | Standard planned presentation. |
| **Level 2** | **Production-Build Fallback** | Mode B backend (`127.0.0.1:8000`) with CORS (`4173`) + Vite preview server (`127.0.0.1:4173`) with direct API base URL. | Vite dev proxy fails, port 5173 is conflicted, or production asset bundling is desired. |
| **Level 3** | **Direct API Evidence Fallback** | Backend running (`127.0.0.1:8000`) + PowerShell `Invoke-RestMethod` / `curl` commands in terminal. | Display server, browser rendering, or frontend crashes occur during presentation. |
| **Level 4** | **Honest Degraded Reporting** | Transparently display `analytics: unavailable` or HTTP 503. | Dataset loading fails or artifact is missing. **Never substitute synthetic fixtures or screenshots as live assessments.** |

---

## 10. Independent Teammate Reproduction — PENDING

**Status: PENDING / NOT YET EXECUTED**

- **Planned operator:** Igor
- **Required evidence:** Igor independently follows `README.md` and `docs/demo_runbook.md` without hidden oral coaching and demonstrates:
  - Configured backend reaches `analytics: "ready"`;
  - Default collection contains the expected 18 replay batches;
  - Frontend queue loads;
  - Queue item selection works;
  - Manual `BAT-000901` lookup works;
  - Any undocumented step/question is reported;
  - Approximate time to working demo is recorded.

This evidence is intentionally deferred to **VLD-04B — Independent Reproduction Closure** and is **not** claimed by VLD-04A.

---

## 11. Deployment Decision VLD04-D1 — ACCEPTED Local-First

### Decision Status
- **Decision Code:** `VLD04-D1 — Demo Operating Mode`
- **Status:** **ACCEPTED by Human Integrator Vladimir**
- **Decision:** **Option A — Local-first authoritative demo**

### Meaning & Boundaries
- **Primary judged demo:** Local Mode B backend + local frontend on presenter laptop.
- **Fallback:** Local production frontend build via `vite preview` + direct local API + explicit CORS configuration.
- **Remote deployment:** **DEFERRED / NOT REQUIRED for the current demo candidate** unless a later explicit organizer requirement or concrete presentation need changes that decision.
- No Render/Docker/cloud/deployment infrastructure files are created or required.

### Rationale
1. Zero demo-time Internet dependency (immune to hackathon venue Wi-Fi congestion or collapse).
2. Pinned sponsor dataset and baseline artifact are guaranteed local and immediate.
3. No cloud cold-start or remote-host lifecycle dependency during the authoritative demo.
4. No cross-origin production hosting topology, reverse proxy, or SSL certificate management required.
5. VLD-03 and VLD-04 have already proven this configuration end-to-end with high stability.

---

## 12. Documentation Reconciliation

Four documentation and template paths were reconciled with the committed product state:

1. **`README.md`:**
   - Removed stale statements claiming that ranked collection routes, facility filtering, and frontend queue consumption do not exist.
   - Accurately described the real single-batch route (`/assessments/{batch_id}`), ranked collection route (`/assessments`), 48-hour UTC+03 replay window, and React operator queue.
   - Clarified that frontend does not currently expose facility/window/pagination UI controls, even though the backend collection API supports them.
   - Replaced `npm install` with `npm ci` for clean lockfile reproduction.
   - Preserved all accepted product limitations and historical chronology.
2. **`.env.example`:**
   - Added template variables: `SMART_HARVEST_DATA_DIR`, `SMART_HARVEST_BASELINE_ARTIFACT`, `VITE_API_BASE_URL`, and `SMART_HARVEST_CORS_ORIGINS` with clear explanatory comments.
3. **`docs/demo_runbook.md`:**
   - Promoted Mode B to the primary demonstration path.
   - Added clean installation steps, UI interaction walkthrough, the 4-level fallback ladder, and teardown/reset procedures.
4. **`docs/integration_contract.md`:**
   - Reconciled VLD-03 status to `ACCEPTED / EVIDENCE COMPLETE / HUMAN INTEGRATED` (PR #53, merge commit `4363e372...`).
   - Acknowledged VLD-05A as `HUMAN INTEGRATED` through PR #54 (`a177c20...`).
   - Recorded VLD-04A branch status as `EVIDENCE RECORDED / READY FOR HUMAN REPOSITORY GATE`.
   - Recorded parent VLD-04 gate as `BLOCKED: MISSING EVIDENCE` (independent reproduction).

---

## 13. Known Operational Limitations

The candidate strictly preserves all accepted product boundaries:
- `deterioration_horizon` is `null` (not estimable from supplied observations; no countdown claimed).
- `factors` is `[]` (deterministic crop-median baseline provides no per-assessment causal attribution).
- `recommendation` is `null` (action recommendations unavailable; prioritisation is not prescription).
- Severity score is a relative ranking index `[0, 1]`, not a calibrated probability, confidence score, or guaranteed future loss.
- Pinned simulation provenance banner remains visible in all modes.
- No production learned model is selected or deployed.
- No production live deployment is claimed.

---

## 14. Shared-Change Audit

Strictly non-modifying for code and infrastructure:

| Component | Status | Notes |
| --- | --- | --- |
| `backend/**` | **UNCHANGED** | Zero Python source edits. |
| `frontend/**` | **UNCHANGED** | Zero TypeScript/React/CSS edits. |
| `scripts/**` | **UNCHANGED** | Zero script edits. |
| `.github/**` | **UNCHANGED** | Zero CI workflow edits. |
| `package.json` / lockfiles | **UNCHANGED** | Zero dependency edits. |
| `backend/pyproject.toml` | **UNCHANGED** | Zero dependency edits. |
| API / Domain Schemas | **UNCHANGED** | Zero contract modifications. |
| Runtime behavior | **UNCHANGED** | Purely operational evaluation and doc reconciliation. |
| Infrastructure files | **NONE ADDED** | No Dockerfile, compose, or cloud manifests added. |

Authorized file changes: strictly 5 documentation and configuration template files:
1. `docs/recon/VLD-04-runtime-demo-readiness.md` (NEW)
2. `docs/demo_runbook.md`
3. `docs/integration_contract.md`
4. `README.md`
5. `.env.example`

---

## 15. Current VLD-04 Gate Status

- **VLD-04A Slice Status:** **OPERATIONAL EVIDENCE RECORDED / READY FOR HUMAN REPOSITORY GATE**
  - All local operational prerequisites, Mode B startup, preview fallback, and documentation drift are verified and reconciled.
- **VLD04-D1 Human Gate:** **ACCEPTED by Human Integrator Vladimir** (Option A — Local-first authoritative demo).
- **Parent VLD-04 Gate Status:** **BLOCKED: MISSING EVIDENCE**
  - **Only remaining blocker:** Independent teammate reproduction.
  - Planned closure: **VLD-04B — Independent Reproduction Closure** (Operator: Igor).
  - No claim is made that Igor has executed the runbook yet.
