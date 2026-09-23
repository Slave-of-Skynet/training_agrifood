# Smart Harvest foundation

Smart Harvest is a **SIMULATION / training challenge** prototype for post-harvest decision support. The repository contains a synthetic fixture demo, a dataset-backed deterministic-baseline single-batch API, and a backend-ranked assessment queue consumed by a React operator frontend.

## What exists

- FastAPI backend with:
  - `GET /api/v1/health`: tri-state analytics health reporting (`not_configured`, `ready`, `unavailable`).
  - `GET /api/v1/demo/assessment`: synthetic contract fixture marked `SIMULATION / synthetic fixture / not challenge data` (`status: insufficient_data`).
  - `GET /api/v1/assessments/{batch_id}`: dataset-backed deterministic-baseline single-batch assessment route (RBS-01 / PR #42) serving Season-2025 held-out batches with `Cache-Control: no-store`.
  - `GET /api/v1/assessments`: ranked multi-batch collection assessment route (IGR-05B / PR #49, TEMP-R1 / PR #51) with configurable half-open dispatch window (defaulting to the accepted 48-hour UTC+03 replay window: `2025-11-29T00:00:00+03:00` to `2025-12-01T00:00:00+03:00`), optional facility filtering, global `risk.score DESC, batch_id ASC` ranking, and pagination.
- Pydantic output contracts for assessment status, risk, deterioration horizon, factors, structured recommendations, reliability, and provenance.
- React + TypeScript + Vite operator shell (PUX-11A / PR #46, PUX-12A / PR #52) with loading, available, and unavailable backend states. The frontend consumes `/api/v1/health`, auto-loads the ranked replay queue via `/api/v1/assessments` when analytics is ready, supports direct queue selection without refetching, and provides independent manual single-batch lookup (`/api/v1/assessments/{batch_id}`). Note: the frontend requests the default replay collection and does not currently expose interactive facility filtering or pagination controls in the UI, even though the backend collection route supports them.
- Raw dataset ingestion and physical structural diagnostics for the sponsor CSV tables ([`backend/app/ingestion/`](backend/app/ingestion/)).
- Typed canonical `BatchAssessmentInput` domain models ([`backend/app/domain/batch.py`](backend/app/domain/batch.py)) and deterministic raw-to-canonical mapper ([`backend/app/ingestion/canonical_mapper.py`](backend/app/ingestion/canonical_mapper.py)), enforcing dispatch-time cutoffs ($T_{assess} \equiv T_{dispatch}$), leakage-safe exclusion of future arrival/transit/outcome fields, preservation of structural missingness as `None`, and planned logistics mapping.
- Offline baseline artifact generator ([`scripts/generate_baseline_artifact.py`](scripts/generate_baseline_artifact.py)) and versioned JSON baseline artifact ([`backend/artifacts/baseline-crop-median-v1-p1-s2024.json`](backend/artifacts/baseline-crop-median-v1-p1-s2024.json)).
- FastAPI lifespan runtime validation of pinned snapshot and baseline artifact ([`backend/app/runtime/`](backend/app/runtime/)).
- Canonical architecture, data-contract, evaluation, domain-rule, and runbook documentation under [`docs/`](docs/).

## What does not exist yet

While raw ingestion, canonical input mapping, offline baseline fitting, single-batch baseline serving, backend collection ranking, and the frontend priority queue are implemented, the repository does not have:
- Frontend UI controls for facility filtering or pagination (the backend collection API supports query parameters, but the browser UI renders the default replay cohort);
- Action recommendation engine (`recommendation` remains `None`);
- Deterioration timing prediction (`deterioration_horizon` remains `None`);
- Contributing factor attribution for the baseline (`factors` remains `[]`);
- Production learned model (no machine learning model selected);
- External persistence layer (database/ORM);
- Authentication, realtime streaming, or production deployment.

## Prerequisites

- Python 3.11+
- Node.js 20.19+ or 22.12+ and npm

## Run the backend

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".\backend[test]"
```

### Unconfigured startup (default)

```powershell
python -m uvicorn app.main:app --app-dir backend --reload
```

- `GET /api/v1/health` returns `analytics: "not_configured"`.
- `GET /api/v1/demo/assessment` returns the synthetic fixture.
- `GET /api/v1/assessments/{batch_id}` returns HTTP 503 ("Analytics runtime unavailable").

### Configured runtime (dataset-backed baseline)

Configure the accepted environment variables before launching:

```powershell
$env:SMART_HARVEST_DATA_DIR = "sponsor_pack/data"
$env:SMART_HARVEST_BASELINE_ARTIFACT = "backend/artifacts/baseline-crop-median-v1-p1-s2024.json"
python -m uvicorn app.main:app --app-dir backend --reload
```

- `GET /api/v1/health` returns `analytics: "ready"`.
- `GET /api/v1/assessments/BAT-000901` returns HTTP 200 with dataset-backed baseline assessment (`status: assessed`, `risk.score: 0.0644`). Note: `BAT-000901` is a recorded Season-2025 training-challenge batch, not a production live batch.
- Season-2024 training batches return HTTP 409 (release ineligible).

## Run the frontend

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to `http://localhost:8000` in development. To use another API origin, copy `.env.example` to `.env` and set `VITE_API_BASE_URL`.

When backend analytics is ready, the frontend operator shell automatically loads the ranked replay queue from `GET /api/v1/assessments`, allows selecting batches for review without refetching, and supports manual single-batch lookup via `GET /api/v1/assessments/{batch_id}`.

The backend's allowed frontend origins can be configured with the `SMART_HARVEST_CORS_ORIGINS` environment variable (comma-separated; default: `http://localhost:5173`).

## Checks

Before running checks, complete the dependency setup above: create and activate `.venv`, install the backend with `python -m pip install -e ".\backend[test]"`, and run `npm ci` in `frontend`. The editable backend installation is required for pytest to import `app`.

The preferred full local repository verification gate for the Windows-first team is, from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

It runs the backend pytest suite using the project `.venv`, then the frontend production build. It does not install dependencies. CI performs clean dependency installation separately before running its checks.

For targeted or manual checks, with `.venv` activated, start from the repository root:

```powershell
python -m pytest backend/tests
cd frontend
npm run build
```

The backend tests validate endpoints (health, demo fixture, single-batch assessment, and collection assessment) and enforce domain contract behavior and invariants. The frontend build runs TypeScript checking before bundling.

See [`scripts/README.md`](scripts/README.md) for script lifecycle and evidence reproduction rules.

## Canonical documentation

- [`docs/challenge_canon.md`](docs/challenge_canon.md) — challenge facts, outcomes, evaluation criteria, and unknowns.
- [`docs/architecture.md`](docs/architecture.md) — accepted system shape and boundaries.
- [`docs/integration_contract.md`](docs/integration_contract.md) — workstream dependency map, integration boundaries, and STOP conditions.
- [`docs/assumptions_unknowns.md`](docs/assumptions_unknowns.md) — unresolved dataset and environment questions.
- [`docs/data_contract.md`](docs/data_contract.md) — current output/application contract.
- [`docs/evaluation.md`](docs/evaluation.md) — evaluation principles without unsupported targets.
- [`docs/domain_rules.md`](docs/domain_rules.md) — guardrails for future agronomic rules.
- [`docs/demo_runbook.md`](docs/demo_runbook.md) — local-first demo and fallback procedure.
- [`docs/team_roles.md`](docs/team_roles.md) — current SoS challenge-specific ownership.
- [`docs/workstreams/`](docs/workstreams/) — SoS challenge-specific operating guides for the five team workstreams.
- [`docs/decisions/0001-foundation-architecture.md`](docs/decisions/0001-foundation-architecture.md) — foundation ADR.
- [`docs/decisions/0002-predictive-input-semantics.md`](docs/decisions/0002-predictive-input-semantics.md) — canonical predictive input semantics decision (ADR 0002).
- [`docs/decisions/0003-assessment-evaluation-semantics.md`](docs/decisions/0003-assessment-evaluation-semantics.md) — assessment, ranking, and evaluation semantics decision (ADR 0003).
- [`docs/decisions/0005-runtime-baseline-serving.md`](docs/decisions/0005-runtime-baseline-serving.md) — runtime baseline serving decision (ADR 0005).
- [`docs/decisions/0006-source-time-semantics.md`](docs/decisions/0006-source-time-semantics.md) — source-local UTC+03 timestamp semantics decision (ADR 0006).
- [`docs/decisions/0007-frontend-ranked-queue-ux.md`](docs/decisions/0007-frontend-ranked-queue-ux.md) — frontend ranked queue UX decision (ADR 0007).
- [`docs/data_recon/01_dataset_inventory.md`](docs/data_recon/01_dataset_inventory.md) — accepted dataset inventory and integrity profile (VDR-01).
- [`docs/data_recon/02_temporal_leakage.md`](docs/data_recon/02_temporal_leakage.md) — accepted temporal semantics and leakage audit (VDR-02).
- [`docs/data_recon/03_target_horizon_feasibility.md`](docs/data_recon/03_target_horizon_feasibility.md) — accepted target and deterioration-horizon feasibility evidence (VDR-03).
- [`docs/data_recon/04_dispatch_predictability.md`](docs/data_recon/04_dispatch_predictability.md) — accepted dispatch predictability benchmark evidence (VDR-04A).
- [`docs/product_recon/`](docs/product_recon/) — product and domain research evidence (APR-01; research notes, not automatically challenge canon).

The sponsor pack supplies an inspectable raw schema. Observed integrity of the supplied snapshot has been profiled in accepted, integrated [VDR-01](docs/data_recon/01_dataset_inventory.md), temporal/leakage semantics have been audited in accepted, integrated [VDR-02](docs/data_recon/02_temporal_leakage.md), and target & deterioration-horizon feasibility has been profiled in accepted, integrated [VDR-03](docs/data_recon/03_target_horizon_feasibility.md). Canonical predictive-input semantics and the `BatchAssessmentInput` definition were accepted under [ADR 0002](docs/decisions/0002-predictive-input-semantics.md) (VLD-02A), and canonical mapping is implemented in application code (IGR-03). Assessment, ranking, baseline, and evaluation semantics were accepted under [ADR 0003](docs/decisions/0003-assessment-evaluation-semantics.md). Single-batch baseline serving was accepted under [ADR 0005](docs/decisions/0005-runtime-baseline-serving.md) and implemented in code (RBS-01 / PR #42). Multi-batch collection serving with source-local UTC+03 replay window was accepted under ADR 0006 and implemented in code (IGR-05B / PR #49, TEMP-R1 / PR #51). Frontend consumption of the ranked collection queue and manual single-batch lookup was accepted under [ADR 0007](docs/decisions/0007-frontend-ranked-queue-ux.md) and implemented in code (PUX-11A / PR #46, PUX-12A / PR #52). Action recommendations, deterioration horizon prediction, and learned models remain separately unbuilt.
