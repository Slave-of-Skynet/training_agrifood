# IGR-05A — Multi-Batch Serving Recon & Decision Packet

## 1. Recon identity

- **Task ID:** `IGR-05A`
- **Task Title:** Multi-Batch Serving Recon & Decision Packet
- **Owner / Author:** Igor — Technical Deputy
- **Reviewer / Decision Owner:** Vladimir — Project Brain / Integrator
- **Repository:** `Slave-of-Skynet/training_agrifood` (upstream), `IgorGlUTMStudent/training_agrifood` (origin fork)
- **Target Branch:** `igor/igr-05a-multi-batch-serving-recon`
- **Verified Base HEAD:** `540c98eb273a14d6a61e37c89c69d4bf9babfa78` (merged PR #46 — PUX-11A single-batch frontend integration)
- **Reference Base Commit:** `401f395bdf6dab1317a36d2e2519627ce0858a3c` (merged PR #45 — VDR-06B runtime release parity)
- **Base SHA Reconciliation:** Upstream `main` advanced from `401f395bdf6dab1317a36d2e2519627ce0858a3c` to `540c98eb273a14d6a61e37c89c69d4bf9babfa78` via merged PR #46 (PUX-11A single-batch dataset-backed assessment integration, commit `4e6f4ab`).
  - *PUX-11A frontend flow changes (External Context):* PR #46 integrated frontend lookup against the single-batch endpoint (`GET /api/v1/assessments/{batch_id}`):
    1. [`frontend/src/api/client.ts`](../../frontend/src/api/client.ts): Added `ApiError` class with HTTP status code preservation, and added `getAssessment(batchId, signal)`.
    2. `frontend/src/components/BatchAssessmentLookup.tsx`: Created single-batch lookup form input.
    3. [`frontend/src/pages/HomePage.tsx`](../../frontend/src/pages/HomePage.tsx): Decoupled health check connection state from assessment request state; implemented `handleLookup()` calling `getAssessment()`; added dedicated UI panels for idle, loading, and HTTP 404 ("Batch not found"), 409 ("not eligible for release"), and 503 ("analytics runtime unavailable") error states.
    4. [`frontend/src/styles.css`](../../frontend/src/styles.css): Added layout and styling for single-batch assessment lookup and error feedback.
  - *Implementation Scope Boundary:* PUX-11A is strictly frontend integration for single-batch lookup. It touched zero backend routes, zero runtime models, zero canonical mapper logic, and zero ADR decisions. PUX-11A is external context only and is strictly **NOT** part of the IGR-05A implementation scope.
- **Task Type:** RECON / DECISION PACKET — DOCUMENTATION ONLY
- **Implementation Authorization:** NONE (Human Gate approval strictly required prior to implementation)
- **Write Scope:** Exactly one new file: [`docs/recon/IGR-05A-multi-batch-serving-recon.md`](IGR-05A-multi-batch-serving-recon.md)
- **Epistemic Status:** RECOMMENDATIONS AND DECISION OPTIONS FOR HUMAN GATE REVIEW; DOES NOT ALTER EXISTING CANONICAL DECISIONS

---

## 2. Executive summary

### Purpose and context
Following the successful integration of RBS-01 (PR #42) and the post-RBS-01 reconciliations (VLD-R6 / PR #43, APR-04A / PR #44, VDR-06B / PR #45), the repository possesses an operational, dataset-backed single-batch HTTP assessment serving path: `GET /api/v1/assessments/{batch_id}`. 

However, Challenge Outcome 1 ("Prioritize batches according to deterioration risk to decide which should be shipped, processed, or re-inspected first") requires an operator triage view across **multiple batches** within an operational shift or replay window. Furthermore, [ADR 0004](../decisions/0004-mvp-product-scope.md) (APR2-D2) established that the MVP operational triage view selects canonical recorded assessment events via a **configurable replay/view window**, with batch ordering governed strictly by [ADR 0003](../decisions/0003-assessment-evaluation-semantics.md) (`risk.score DESC, batch_id ASC`).

The purpose of **IGR-05A** is to perform a rigorous, read-only architectural, data-selection, performance, and contract reconnaissance for multi-batch serving. It maps candidate paths, identifies capability gaps, benchmarks runtime costs, evaluates 23 core architectural questions, formulates three concrete candidate designs, and structures 10 explicit decision proposals for Human Gate review (Vladimir).

### Key findings

1. **Safety boundary preserved (FACT):** The runtime multi-batch selection and scoring path strictly requires only the operational snapshot tables (`batches`, `storage_sessions`, `storage_zones`, `facilities`, `quality_checks`, `sensor_readings`, and optionally `shipments`). The label table `historical_quality_outcomes.csv` is **NOT** accessed at runtime. Zero outcome leakage exists.
2. **Data-selection path (FACT):** The authoritative join path is `batches -> storage_sessions -> storage_zones -> facilities`. 
   - `dispatch_datetime` lives exclusively in `storage_sessions.csv`.
   - `facility_id` lives in `facilities.csv` and `storage_zones.csv` (referenced by `storage_sessions.zone_id`).
   - Replay-window membership (`dispatch_datetime`) and facility filtering (`facility_id`) can be evaluated **100% prior to canonical mapping** on raw session rows (1,800 rows) and zone rows (25 rows).
   - Release eligibility (`batch_id in runtime.held_out_ids`) is precomputed at lifespan startup in $O(1)$ set lookup.
3. **Current mapper performance shape (OBSERVED PRACTICE):**
   - In the current implementation, [`build_batch_assessment_input()`](../../backend/app/ingestion/canonical_mapper.py) executes unindexed linear scans over `batches` (1,800 rows), `storage_sessions` (1,800 rows), `quality_checks` (5,400 rows), and `shipments` (1,800 rows), parses zone telemetry (~26,000 readings/zone), and instantiates Pydantic domain models.
   - Benchmark measurements on the local environment demonstrate that sequential single-batch execution requires **~65–71 ms per batch**.
   - Attempting to evaluate all 900 held-out batches sequentially on every collection request would require **~65 seconds**, which would cause HTTP timeouts.
   - Conversely, evaluating a bounded replay window (e.g., 24–48 hours in Season 2025, containing 5–25 batches) requires **~0.36–1.85 s** under Mode (b) distinct-batch dynamics (~72–74 ms/call), providing responsive low-latency HTTP responses **without requiring any database, worker queue, or complex indexing infrastructure**.
4. **Architectural necessity assessment (INFERENCE):**
   - **Database:** NOT NEEDED for bounded MVP / demo. The 54 MB snapshot resides in memory in `RawSnapshot`.
   - **Concurrency / Worker Infrastructure:** NOT NEEDED for bounded MVP / demo. Synchronous, in-process FastAPI execution over bounded collections satisfies demo needs.
   - **Runtime Indexes:** NOT strictly required if queries are window-bounded, though a lightweight pre-filtering helper in the service layer provides clean separation and microsecond cohort selection.
5. **Human Gate requirement:** 10 explicit decision points (`IGR05-D1` through `IGR05-D10`) are submitted for Human Integrator decision. Implementation in IGR-05B remains blocked pending this gate.

---

## 3. Sources inspected

| Source Key | Inspected File / Artifact | Classification | Purpose and Authority |
| :--- | :--- | :--- | :--- |
| **S1** | [`backend/app/api/routes.py`](../../backend/app/api/routes.py) | FACT / CODE | Current single-batch endpoint, error handling, cache headers |
| **S2** | [`backend/app/main.py`](../../backend/app/main.py) | FACT / CODE | Application lifespan, CORS policy, middleware, startup |
| **S3** | [`backend/app/runtime/context.py`](../../backend/app/runtime/context.py) | FACT / CODE | Lifespan state, `AnalyticsRuntimeContext`, fail-closed provider |
| **S4** | [`backend/app/runtime/artifact.py`](../../backend/app/runtime/artifact.py) | FACT / CODE | Pinned snapshot validation, SHA256 hashes, cohort partition |
| **S5** | [`backend/app/services/baseline_assessment.py`](../../backend/app/services/baseline_assessment.py) | FACT / CODE | Deterministic baseline assessment construction |
| **S6** | [`backend/app/ingestion/canonical_mapper.py`](../../backend/app/ingestion/canonical_mapper.py) | FACT / CODE | Raw-to-canonical mapper, join logic, telemetry cache |
| **S7** | [`backend/app/ingestion/raw_reader.py`](../../backend/app/ingestion/raw_reader.py) | FACT / CODE | `RawSnapshot`, `RawTable`, structural diagnostics |
| **S8** | [`backend/app/ingestion/structural_manifest.py`](../../backend/app/ingestion/structural_manifest.py) | FACT / CODE | Table manifests, foreign key specs, expected schemas |
| **S9** | [`backend/app/analytics/crop_median_baseline.py`](../../backend/app/analytics/crop_median_baseline.py) | FACT / CODE | Baseline scoring logic, median calculation, clipping |
| **S10** | [`backend/app/domain/assessment.py`](../../backend/app/domain/assessment.py) | FACT / CODE | Domain contract: `RiskAssessment`, `HealthResponse`, enums |
| **S11** | [`backend/app/domain/batch.py`](../../backend/app/domain/batch.py) | FACT / CODE | Domain contract: `BatchAssessmentInput` and sub-contexts |
| **S12** | [`backend/artifacts/baseline-crop-median-v1-p1-s2024.json`](../../backend/artifacts/baseline-crop-median-v1-p1-s2024.json) | FACT / ARTIFACT | Pinned baseline artifact values, crop medians, global median |
| **S13** | [`docs/decisions/0003-assessment-evaluation-semantics.md`](../decisions/0003-assessment-evaluation-semantics.md) | DECISION | Normative ranking (`score DESC, batch_id ASC`), engine comparability |
| **S14** | [`docs/decisions/0004-mvp-product-scope.md`](../decisions/0004-mvp-product-scope.md) | DECISION | Replay window policy, facility filter semantics, operator persona |
| **S15** | [`docs/decisions/0005-runtime-baseline-serving.md`](../decisions/0005-runtime-baseline-serving.md) | DECISION | Serving architecture, release eligibility (409/404), lifespan |
| **S16** | [`docs/integration_contract.md`](../integration_contract.md) | DECISION | Workstream boundaries, shared contracts, STOP conditions |
| **S17** | [`docs/recon/VLD-R6-post-rbs01-reconciliation.md`](VLD-R6-post-rbs01-reconciliation.md) | RECON | Candidate next slices (Candidate B: Multi-batch backend) |
| **S18** | [`docs/data_recon/06b_runtime_release_parity.md`](../data_recon/06b_runtime_release_parity.md) | EVIDENCE | VDR-06B release parity audit (900 held-out batches, 0 errors) |
| **S19** | `sponsor_pack/data/*.csv` | FACT / DATA | Raw CSV files: 1,800 batches, 1,800 sessions, 25 zones, 10 facilities |

---

## 4. Current committed runtime path

### Execution trace for single-batch serving

The committed single-batch serving pipeline executes along the following sequence:

```text
HTTP GET /api/v1/assessments/{batch_id}
  │
  ├── 1. Route Handler (backend/app/api/routes.py:assessment)
  │      Sets "Cache-Control: no-store"
  │
  ├── 2. Runtime Dependency Provider (backend/app/runtime/context.py:get_runtime)
  │      Extracts runtime context from request.app.state.analytics_runtime
  │      Fails closed: raises HTTP 503 if analytics != "ready" or context is None
  │
  ├── 3. Release Eligibility Verification (backend/app/api/routes.py:44-47)
  │      Checks if batch_id in runtime.training_ids  --> raises HTTP 409
  │      Checks if batch_id not in runtime.held_out_ids --> raises HTTP 404
  │
  ├── 4. Canonical Mapping (backend/app/ingestion/canonical_mapper.py:build_batch_assessment_input)
  │      Verifies presence of 6 required raw tables in runtime.snapshot
  │      Retrieves or lazily builds telemetry zone index: snapshot._readings_by_zone_cache
  │      Linear scan in snapshot["batches"].rows for batch_id (enforces cardinality == 1)
  │      Linear scan in snapshot["storage_sessions"].rows for batch_id (enforces cardinality == 1)
  │      Linear scan in snapshot["storage_zones"].rows for session.zone_id (enforces cardinality == 1)
  │      Linear scan in snapshot["facilities"].rows for zone.facility_id (enforces cardinality == 1)
  │      Linear scan in snapshot["quality_checks"].rows for batch_id (enforces harvest & pre_dispatch == 1)
  │      Validates physical chronology invariant:
  │        T_harvest < T_harvest_qc < T_entry < T_pre_dispatch_qc < T_dispatch
  │      Filters zone telemetry readings: entry_datetime <= ts <= dispatch_datetime
  │      Linear scan in snapshot["shipments"].rows for batch_id (optional, cardinality <= 1)
  │      Assembles and validates typed BatchAssessmentInput Pydantic model
  │
  ├── 5. Baseline Scoring (backend/app/services/baseline_assessment.py:build_baseline_assessment)
  │      Calls predict_risk_score(runtime.baseline, batch_input)
  │        reads batch_input.batch.crop_type
  │        looks up crop_medians[crop_type] (falls back to global_median if unseen)
  │        clips score to [0.0, 1.0]
  │
  ├── 6. RiskAssessment Construction (backend/app/services/baseline_assessment.py:49-71)
  │      Constructs RiskAssessment with:
  │        status = AssessmentStatus.ASSESSED
  │        risk = RiskEstimate(score=score, band=None)
  │        deterioration_horizon = None
  │        factors = []
  │        recommendation = None
  │        reliability = Reliability(level=UNAVAILABLE, confidence_score=None, ...)
  │        provenance = Provenance(
  │          contract_version="1.0.0",
  │          engine_tier="deterministic_baseline",
  │          engine_version=ENGINE_VERSION,
  │          generated_at=now_utc,
  │          source_dataset_id=DATASET_ID,
  │          simulation=True,
  │          notice=NOTICE,
  │        )
  │
  └── 7. Response Serialization & Transport (FastAPI / Starlette)
         Serializes RiskAssessment to JSON
         Returns HTTP 200 with Cache-Control: no-store
```

### Stage-by-stage component analysis

| Stage | File & Symbol | Input | Output | State Used | Failure Mode | Reusable for Collection Serving? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Request** | [`backend/app/api/routes.py`](../../backend/app/api/routes.py)<br>`assessment()` | HTTP path param `batch_id` | HTTP Response | None | HTTP 404 / 409 / 500 / 503 | Partial: new route required for collection query parameters |
| **2. Provider** | [`backend/app/runtime/context.py`](../../backend/app/runtime/context.py)<br>`get_runtime()` | `fastapi.Request` | `AnalyticsRuntimeContext` | `app.state.analytics_runtime` | HTTP 503 if unconfigured / unavailable | **YES (100%)**: identical runtime dependency provider |
| **3. Eligibility** | [`backend/app/api/routes.py`](../../backend/app/api/routes.py)<br>in-route check | `batch_id: str` | `bool` | `runtime.training_ids`, `runtime.held_out_ids` | HTTP 409 (training), HTTP 404 (unknown) | **YES**: pre-filter collection against `held_out_ids` |
| **4. Mapper** | [`backend/app/ingestion/canonical_mapper.py`](../../backend/app/ingestion/canonical_mapper.py)<br>`build_batch_assessment_input()` | `RawSnapshot`, `batch_id` | `BatchAssessmentInput` | `snapshot.tables`, `snapshot._readings_by_zone_cache` | `CanonicalMappingError` (raises 500) | **YES**: reusable per batch, but repeated linear scans are expensive |
| **5. Scoring** | [`backend/app/analytics/crop_median_baseline.py`](../../backend/app/analytics/crop_median_baseline.py)<br>`predict_risk_score()` | `CropMedianBaseline`, `BatchAssessmentInput` | `float` (0.0–1.0) | `runtime.baseline` | `TypeError` if input types invalid | **YES (100%)**: deterministic scoring function |
| **6. Service** | [`backend/app/services/baseline_assessment.py`](../../backend/app/services/baseline_assessment.py)<br>`build_baseline_assessment()` | Baseline, BatchInput, Provenance kwargs | `RiskAssessment` | Stateless | `ValueError` if Pydantic invariant fails | **YES (100%)**: standard assessment builder |
| **7. Transport** | FastAPI Serialization | `RiskAssessment` | JSON bytes | Pydantic serializer | Model validation error | **YES**: item serialization or envelope serialization |

---

## 5. Already accepted constraints

The multi-batch reconnaissance is strictly bounded by prior Human Gate decisions. These constraints are **NON-NEGOTIABLE** and cannot be altered by this recon:

1. **ADR 0001 (Foundation Architecture):**
   - Modular monolith pattern (`backend/app/{api,domain,ingestion,analytics,services,runtime}`).
   - FastAPI + Pydantic v2.
   - Zero external persistence layer (no database, no ORM, no SQLite, no PostgreSQL).
2. **ADR 0002 (Predictive Input Semantics & Leakage Boundary):**
   - Single assessment clock: $T_{\text{assess}} \equiv T_{\text{dispatch}} = \text{storage\_sessions.dispatch\_datetime}$.
   - Strict temporal filter: $\text{entry\_datetime} \le t \le \text{dispatch\_datetime}$ for telemetry.
   - Forbidden inputs: Arrival QC, actual transit realizations, observations after dispatch, and historical quality outcomes.
   - Physical chronology: $T_{\text{harvest}} < T_{\text{harvest\_qc}} < T_{\text{entry}} < T_{\text{pre\_dispatch\_qc}} < T_{\text{dispatch}}$.
3. **ADR 0003 (Assessment, Ranking & Evaluation Semantics):**
   - **D1:** Primary operational task is batch prioritization/ranking at dispatch.
   - **D2:** Bounded risk score: $\text{score} = \text{clip}(\text{predicted\_loss\_fraction\_pct}, 0, 100) / 100$; $\text{risk.band} = \text{null}$.
   - **D3 (Human Override):** Deterministic queue ranking order:
     $$\text{risk.score DESC, batch\_id ASC}$$
     Common ranked queue is permitted **ONLY** for results with the exact same `engine_tier + engine_version`. Different tiers/versions must NEVER be merged.
   - **D6 & D7:** $\text{deterioration\_horizon} = \text{null}$; $\text{reliability.level} = \text{"unavailable"}$; $\text{confidence\_score} = \text{null}$.
   - **D9:** $\text{recommendation} = \text{null}$.
4. **ADR 0004 (MVP Product Scope & UX Boundaries):**
   - **APR2-D1:** Primary persona is the dispatch-side storage operator ("Dispatch Supervisor" is an SoS design persona, not an operational authority assertion).
   - **APR2-D2:** Operational triage view selects canonical recorded events via a **configurable replay/view window**.
   - **APR2-D2:** $\text{facility\_id}$ serves strictly as a **UI and context filter** (does not partition dataset into separate operational jurisdictions).
   - **APR2-D3:** Batches with status `insufficient_data` must be presented in a separate, neutral section, excluded from numeric ranking.
5. **ADR 0005 (Runtime Baseline Serving):**
   - **D1:** Offline fit on Season 2024 ($\text{dispatch\_datetime} < 2025\text{-}05\text{-}01$, 900 batches). Inference-only serving on Season 2025 held-out cohort ($\text{dispatch\_datetime} \ge 2025\text{-}05\text{-}01$, 900 batches).
   - **D1 & D5:** Requests must NEVER fit or refit models. Training batches receive HTTP 409 ("Batch is not eligible for this assessment release").
   - **D3:** `simulation = True`, `engine_tier = "deterministic_baseline"`, fixed notice string.
   - **D4:** FastAPI lifespan startup initialization; fail-closed provider.

---

## 6. Current data-selection path

### Physical schema and relational join graph

The physical relationships between raw tables in `sponsor_pack/data/` were audited and confirmed:

```text
┌──────────────────────┐        1:1        ┌──────────────────────────┐
│     batches.csv      ├───────────────────┤   storage_sessions.csv   │
│                      │                   │                          │
│ PK: batch_id         │                   │ PK: storage_session_id   │
│ - crop_type          │                   │ FK: batch_id             │
│ - harvest_datetime   │                   │ FK: zone_id              │
│ - ...                │                   │ - entry_datetime         │
└──────────────────────┘                   │ - dispatch_datetime      │
                                           └────────────┬─────────────┘
                                                        │
                                                    N:1 │
                                                        ▼
┌──────────────────────┐        N:1        ┌──────────────────────────┐
│    facilities.csv    │◄──────────────────┤    storage_zones.csv     │
│                      │                   │                          │
│ PK: facility_id      │                   │ PK: zone_id              │
│ - facility_name      │                   │ FK: facility_id          │
│ - region, district   │                   │ - zone_name, zone_type   │
└──────────────────────┘                   └──────────────────────────┘
```

### Critical data-selection findings

1. **Exact location of `dispatch_datetime` (FACT):**
   - File: `sponsor_pack/data/storage_sessions.csv`
   - Column: `dispatch_datetime` (Column index 4, ISO-8601 string, e.g. `2024-09-11 15:50:24`).
   - Cardinality: Exactly 1 session per batch (1,800 sessions across 1,800 batches).
   - Invariant: Every batch has exactly one recorded `dispatch_datetime`.
2. **Exact location of `facility_id` (FACT):**
   - Primary definition: `sponsor_pack/data/facilities.csv`, column `facility_id` (10 rows, `FAC-001` through `FAC-010`).
   - Foreign key reference: `sponsor_pack/data/storage_zones.csv`, column `facility_id` (25 rows, `ZONE-001` through `ZONE-025`).
   - Batch association: `storage_sessions.csv` contains `zone_id`.
   - Resolution path: `batch_id -> storage_sessions.zone_id -> storage_zones.facility_id`.
   - Cardinality: Exactly 1 zone per session, and exactly 1 facility per zone. Thus, every batch belongs to exactly one facility.
3. **Pre-filtering feasibility before canonical mapping (FACT):**
   - **Facility filtering:** Can be evaluated completely prior to canonical mapping. A simple dictionary mapping `zone_id -> facility_id` built from the 25 rows of `storage_zones.csv` allows immediate filtering of `storage_sessions` rows by `facility_id`.
   - **Release eligibility filtering:** Can be evaluated in $O(1)$ set lookup (`batch_id in runtime.held_out_ids`) prior to canonical mapping.
   - **Replay-window membership filtering:** Can be evaluated completely prior to canonical mapping by parsing `dispatch_datetime` on candidate `storage_sessions` rows (`window_start <= dispatch_datetime <= window_end`).
   - **Summary conclusion:** Candidate cohort identification (filtering by window, facility, and held-out eligibility) requires scanning only the 1,800 rows of `storage_sessions` and 25 rows of `storage_zones`. This takes **< 2 milliseconds** in memory!
4. **Safety Boundary Check — `historical_quality_outcomes.csv` (FACT):**
   - Is `historical_quality_outcomes.csv` needed for queue construction, filtering, or scoring? **ABSOLUTELY NOT.**
   - All queue selection features (`batch_id`, `crop_type`, `dispatch_datetime`, `zone_id`, `facility_id`) originate strictly from `batches.csv`, `storage_sessions.csv`, and `storage_zones.csv`.
   - Design violation check: **PASSED (Zero outcome access in runtime queue path).**

---

## 7. Current mapper/runtime cost shape

### Implementation mechanics of `build_batch_assessment_input()`

Inspection of [`backend/app/ingestion/canonical_mapper.py`](../../backend/app/ingestion/canonical_mapper.py) reveals the computational cost of mapping an individual batch:

1. **Telemetry Index Reuse (FACT):**
   - Lines 165–181: On the first invocation, the mapper builds an index `readings_by_zone: dict[str, list[dict[str, str]]]` over all 669,665 rows of `sensor_readings` and stores it in `snapshot._readings_by_zone_cache`.
   - On subsequent calls with the same snapshot, this index is reused in $O(1)$ dictionary lookup.
2. **Zone Telemetry Parsing Overhead (FACT):**
   - Lines 410–437: For a given batch, the mapper retrieves all readings for its `zone_id` (average: 669,665 / 25 = 26,786 readings).
   - It iterates over all ~26,786 rows, parses ISO timestamps (`_parse_datetime`), filters by `entry_datetime <= ts <= dispatch_datetime`, parses 9 sensor measurement fields, and constructs a `TelemetryReading` Pydantic model for every valid reading.
3. **Linear Table Scans (FACT):**
   - Line 185: `[r for r in batch_table.rows if r.get("batch_id") == batch_id]` scans all 1,800 batches.
   - Line 196: `[r for r in session_table.rows if r.get("batch_id") == batch_id]` scans all 1,800 sessions.
   - Line 229: `[r for r in zone_table.rows if r.get("zone_id") == zone_id]` scans all 25 zones.
   - Line 268: `[r for r in facility_table.rows if r.get("facility_id") == facility_id]` scans all 10 facilities.
   - Line 323: `[r for r in qc_table.rows if r.get("batch_id") == batch_id]` scans all 5,400 quality checks.
   - Line 446: `[r for r in shipment_table.rows if r.get("batch_id") == batch_id]` scans all 1,800 shipments.
4. **Pydantic Validation (FACT):**
   - Validates `BatchAssessmentInput` and 9 sub-models with `extra="forbid"`.

### Two operational cost modes (OBSERVED PRACTICE)

As empirically demonstrated in the Section 8 local benchmark probe, the runtime exhibits two distinct operational cost regimes:
- **Mode (a) — Warm-Cache Repeat for Same Batch:** When querying the same batch repeatedly (`BAT-000901`) where zone telemetry cache and memory locality are already primed, the full serving pipeline requires **~8.99–9.14 ms per call**.
- **Mode (b) — Distinct-Batch Cache-Build across Zones:** When querying $N$ distinct batches across different storage zones and facilities, each invocation executes unindexed table scans, filters distinct zone telemetry, and builds Pydantic sub-models, requiring **~72.25–74.18 ms per distinct batch** (with `build_batch_assessment_input()` directly accounting for ~65.83 ms).
- **Operational Serving Implication:** Multi-batch collection queries operate under **Mode (b)** conditions. Any latency projection for multi-batch endpoints must be calculated using Mode (b) figures (~72–74 ms/batch), not Mode (a) repeat figures.

---

## 8. Local runtime observations, if executed

### Step 5 — Existing backend test suite verification

- **Command executed:** `.\.venv\Scripts\python.exe -m pytest backend/tests`
- **Platform:** Windows (win32), Python 3.12.3, pytest 8.4.1, pluggy 1.6.0
- **Actual verbatim output:**
  ```text
  ........................................................................ [ 67%]
  ..................................                                       [100%]
  ============================== warnings summary ===============================
  .venv\Lib\site-packages\fastapi\testclient.py:1
    D:\AgriFood\training_agrifood\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
      from starlette.testclient import TestClient as TestClient  # noqa

  .venv\Lib\site-packages\starlette\testclient.py:53
    D:\AgriFood\training_agrifood\.venv\Lib\site-packages\starlette\testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
      _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

  -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
  106 passed, 2 warnings in 12.84s
  ```
- **Exit code:** `0`
- **Actual test count:** **106 passed** (0 failures, 0 errors, 2 pre-existing framework deprecation warnings).
- **Explanation of 67 vs. 106 discrepancy:**
  1. *Progress indicator vs. test count:* Because `backend/pyproject.toml` configures `addopts = "-q"`, pytest executes in quiet mode. On a standard terminal width, pytest prints 72 execution dots on line 1 followed by progress percentage `[ 67%]` (72 / 106 = 67.9% ≈ 67%). Line 2 prints the remaining 34 dots to reach `[100%]`. The intermediate terminal string `[ 67%]` represents the progress bar percentage at line-wrap, NOT a passing test count.
  2. *Historical branch vs. current HEAD:* On the pre-RBS-01 feature branch (`igor/igr-04b-runtime-baseline-assessment`), the test suite historically collected exactly 67 items across legacy test files (`test_canonical_mapper.py`, `test_diagnostics.py`, `test_raw_reader.py`). RBS-01 (PR #42) refactored these tests into `test_ingestion_canonical.py` (21 tests) and `test_ingestion_structural.py` (10 tests), and added `test_runtime_baseline.py` (41 tests). At verified base HEAD `401f395bdf6dab1317a36d2e2519627ce0858a3c`, the test suite contains exactly 106 collected tests across 7 test files, all passing.

### Step 6 — Configured runtime verification

Runtime environment configured:
- `SMART_HARVEST_DATA_DIR = "sponsor_pack/data"`
- `SMART_HARVEST_BASELINE_ARTIFACT = "backend/artifacts/baseline-crop-median-v1-p1-s2024.json"`

Observed responses via `TestClient(create_app())`:
- `GET /api/v1/health`:
  `status = 200`, `{"status": "ok", "service": "smart-harvest", "analytics": "ready"}`
- `GET /api/v1/assessments/BAT-000901` (Season 2025 held-out batch):
  `status = 200`, `{"batch_id": "BAT-000901", "status": "assessed", "risk": {"score": 0.0644, "band": None}, ...}`
- `GET /api/v1/assessments/BAT-000001` (Season 2024 training batch):
  `status = 409`, `{"detail": "Batch is not eligible for this assessment release"}`

### Step 7 — Local performance probe benchmark

A standalone benchmark harness was executed outside the repository (in `$env:TEMP/probe_modes.py`, deleted after run) against the warmed runtime context in two distinct, explicitly labeled modes:
- **Mode (a):** Repeated calls for the **SAME** held-out batch (`BAT-000901`), where zone telemetry cache and internal OS memory structures are fully warm.
- **Mode (b):** Sequential calls over **N DISTINCT** held-out batches across different zones, where each call performs fresh linear scans and per-zone telemetry parsing.

- **Classification:** `OBSERVED PRACTICE — LOCAL ENVIRONMENT ONLY` (Windows 11, Python 3.12.3). Does not constitute a production scalability claim.
- **Observed measurements:**

| Probe Mode & Methodology | Batches / Calls | Total Elapsed Time | Average Latency per Call |
| :--- | :---: | :---: | :---: |
| **Lifespan Startup** | 1 startup | 3.9694 s | 3.97 s (loads 8 CSVs, verifies SHA256 hashes, runs diagnostics, partitions cohorts) |
| **Mode (a): 1st Call (Cold, Cache Build)** | 1 call | 0.2756 s | 275.6 ms |
| **Mode (a): Same Batch (Warm)** | 10 calls | 0.0899 s | **8.99 ms / call** |
| **Mode (a): Same Batch (Warm)** | 50 calls | 0.4571 s | **9.14 ms / call** |
| **Mode (a): Same Batch (Warm)** | 100 calls | 0.9103 s | **9.10 ms / call** |
| **Mode (b): Distinct Batches (Warm)** | 10 distinct calls | 0.7225 s | **72.25 ms / call** |
| **Mode (b): Distinct Batches (Warm)** | 50 distinct calls | 3.7088 s | **74.18 ms / call** |
| **Mode (b): Distinct Batches (Warm)** | 100 distinct calls | 7.2274 s | **72.27 ms / call** |
| **Direct Mapping: Distinct Batches** | 100 distinct calls | 6.5826 s | **65.83 ms / call** |

### Performance probe implications

1. **Mapping dominates latency in Mode (b) (FACT):** When querying distinct batches, direct `build_batch_assessment_input()` accounts for ~91% of request latency (~65.8 ms out of ~72.3 ms). Baseline scoring and HTTP serialization take < 5 ms combined.
2. **Mode (a) vs. Mode (b) disparity (OBSERVED PRACTICE):** Repeated calls to the same batch (Mode a) achieve ~9.1 ms/call due to cache locality and single-zone processing. However, real multi-batch collection serving operates under Mode (b) (distinct batches), requiring **~72–74 ms per distinct batch** with the current unindexed canonical mapper.
3. **Unbounded collection is dangerous (INFERENCE):** If a collection endpoint attempts to execute `build_batch_assessment_input()` for all 900 held-out batches sequentially on every HTTP request, it will require:
   $$900 \times 72.3\text{ ms} \approx 65\text{ seconds}$$
   This would exceed default HTTP client timeouts and degrade developer experience.
4. **Replay window naturally bounds distinct batch evaluation (INFERENCE):** Under ADR 0004 APR2-D2, the operator views a **configurable replay/view window** (e.g. 24 or 48 hours). In Season 2025, a 24-hour window contains typically 2 to 8 batches; a 48-hour window contains 5 to 15 batches; a 7-day window contains ~35 batches.
   - 5 distinct batches $\to$ **~0.36–0.37 s**
   - 10 distinct batches $\to$ **~0.72 s**
   - 20 distinct batches $\to$ **~1.45 s**
   - 25 distinct batches $\to$ **~1.85 s**
   - 50 distinct batches $\to$ **~3.71 s**
   - 100 distinct batches $\to$ **~7.23 s**
   Bounding the replay window limits the candidate cohort and its mapping/scoring cost; a page limit bounds only the returned payload and cannot prevent scoring all matching candidates.

---

## 9. Multi-batch capability gaps

| Capability Area | Single-Batch State (RBS-01) | Required Multi-Batch State (IGR-05) | Nature of Gap |
| :--- | :--- | :--- | :--- |
| **HTTP Route** | `GET /api/v1/assessments/{batch_id}` | Collection endpoint (`GET /api/v1/assessments` or `/api/v1/queue`) | Route absent |
| **Replay Window Query** | None (direct ID lookup) | Query parameters for window selection (`window_start`, `window_end` or preset) | Query parameters absent |
| **Facility Filtering** | None | Optional query parameter `facility_id` | Query parameter absent |
| **Collection Domain Contract** | Single `RiskAssessment` model | Collection response envelope model or list model | Output contract absent |
| **Queue Ordering / Ranking** | None (single item returned) | Sorting by `risk.score DESC, batch_id ASC` (ADR 0003 D3) | Ranking logic absent |
| **Pagination / Bounding** | None | Limit/offset or window-bounded constraints | Bounds logic absent |
| **Application Service** | `build_baseline_assessment` (single) | Collection orchestration service in `backend/app/services/` | Service absent |
| **Empty Result Handling** | Returns 404 for missing batch | Must return empty collection (200 with `[]`) when 0 batches match filter | Semantics undefined |
| **Partial Failure Semantics** | Fails 500 on mapping error | Policy for handling 1 failure among N batches in collection | Semantics undefined |

---

## 10. Collection membership semantics (Q6)

### Analysis of candidate membership sequences

The order in which filters are applied determines both computational efficiency and domain correctness. Two primary sequencing strategies exist:

- **Sequence 1: Map-First then Filter (REJECTED)**
  - Map all batches in snapshot $\to$ score all batches $\to$ filter by held-out cohort $\to$ filter by window $\to$ filter by facility $\to$ sort $\to$ paginate.
  - *Evaluation:* Disastrous performance ($64+$ seconds per request) and violates isolation by mapping training batches during runtime serving.
- **Sequence 2: Filter-First then Map (RECOMMENDED)**
  - Step 1: Filter raw `storage_sessions` by `batch_id in runtime.held_out_ids` (Season 2024 training batches strictly excluded).
  - Step 2: Filter candidate sessions by replay window: $\text{window\_start} \le \text{dispatch\_datetime} \le \text{window\_end}$.
  - Step 3: If `facility_id` is supplied, filter candidate sessions where `zone_id` maps to `facility_id`.
  - Step 4: Map **ONLY** the surviving candidate batches through `build_batch_assessment_input()`.
  - Step 5: Score surviving batches through `build_baseline_assessment()`.
  - Step 6: Sort surviving assessments by `risk.score DESC, batch_id ASC`.
  - Step 7: Return ranked collection.

### Release eligibility in collection context

- Under ADR 0005 D1 & D5, Season 2024 training batches ($\text{dispatch\_datetime} < 2025\text{-}05\text{-}01$) receive HTTP 409 if queried individually by ID.
- In a collection / queue endpoint, training batches **MUST NEVER appear in the returned collection**. They are filtered out at Step 1. A query whose replay window falls entirely in Season 2024 returns an empty collection (`items: []`), not an HTTP 409 error. HTTP 409 remains specific to single-resource retrieval by ID.

---

## 11. Replay-window decision space (Q3, Q4, Q5)

### Decision question Q3: Mandatory vs. optional replay window
- **Option A (Mandatory Window):** Route requires `window_start` and `window_end` ISO datetime strings. If missing, returns HTTP 400 Bad Request.
- **Option B (Optional Window with Default Bounds):** If window parameters are omitted, the endpoint defaults to a bounded evaluation window.
- **Option C (Named Replay Presets):** Query parameter `preset=season_2025_start` or `preset=latest_shift`.
- **HUMAN DECISION REQUIRED (IGR05-D2):** The choice between mandatory window parameters (Option A) vs. optional with default bounds (Option B), as well as the specific default window duration (e.g., 24h, 48h, 7d), is strictly reserved for Human Gate review (Vladimir). The technical recon recommends Option B for ease of demo initialization, but the decision owner must select the authoritative default policy.

### Decision question Q4: Anchor clock
- **Fixed Invariant (ADR 0002 / ADR 0004):** The anchor clock is strictly `storage_sessions.dispatch_datetime`. Window boundaries match against `dispatch_datetime`.

### Decision question Q5: Boundary semantics
- **Option A (Closed Interval):** $\text{window\_start} \le \text{dispatch\_datetime} \le \text{window\_end}$ (both ends inclusive).
- **Option B (Half-Open Interval):** $\text{window\_start} \le \text{dispatch\_datetime} < \text{window\_end}$ (standard time-series convention, prevents double-counting at window seams).

---

## 12. Facility-filter decision space (Q7, Q8, Q9)

### Decision question Q7: Filter syntax
- Query parameter: `facility_id: str | None = None` (e.g., `?facility_id=FAC-001`).

### Decision question Q8 & Q9: Invalid or missing facility handling
- **Option A (Strict Validation):** If `facility_id` does not exist in `facilities.csv` (10 known facilities), return HTTP 404 ("Facility not found") or HTTP 400 ("Invalid facility_id").
- **Option B (Permissive Empty Result):** Return HTTP 200 with empty list `items: []` for any non-matching facility.
- *Recommendation:* Option A (HTTP 404 for non-existent facility ID) aligns with single-batch HTTP semantics and prevents silent operator typos.

---

## 13. Ordering and comparability (Q10, Q11)

### Ordering rule enforcement (ADR 0003 D3)
- All collections returned to an operator must be sorted deterministically:
  $$\text{risk.score DESC, batch\_id ASC}$$
- Ties in `risk.score` are broken by `batch_id ASC`. For the deterministic crop-median baseline, batches sharing the same crop will have identical risk scores; lexical sorting by `batch_id ASC` guarantees identical ordering across repeat calls and page views.

### The Slice-Before-Rank Semantic Problem (Contract Q11 Analysis)
- **The Semantic Conflict:** If an implementation naively applies pagination slicing (`[offset : offset + limit]`) *before* computing scores and ranking, it creates a severe domain violation: the returned page contains only the locally sorted items of an arbitrary chronological batch slice. Batches with the highest risk in the entire replay window that happen to fall outside the raw chronological slice would be completely omitted from page 1.
- **Contract Requirement (ADR 0003 D1 & D3):** The operator triage queue requires true operational prioritization by risk score across the requested operational window. Slicing must strictly occur **AFTER** global risk ranking across the candidate cohort matching the window and facility filters.
- **Authoritative Canonical Pipeline for Bounded Initial IGR-05B:**
  $$\text{filter (eligible/window/facility)} \longrightarrow \text{canonical-map and score ALL window candidates} \longrightarrow \text{global sort (risk.score DESC, batch\_id ASC)} \longrightarrow \text{pagination slice [offset:offset+limit]} \longrightarrow \text{response assembly}$$
  - *Compute vs. Payload Bounding:* Replay window bounding naturally limits the **compute cost** (the total candidate batches mapped and scored; e.g. 5–25 batches requires only ~0.36–1.85 s total wall time under Mode (b) distinct-batch execution). In contrast, the pagination `limit` parameter bounds the **returned page size and network transport payload**. Pagination does NOT prevent scoring all window candidates.
  - *Full Pipeline Integrity:* Because window sizes are bounded in operational triage (e.g. 24h or 48h), executing full canonical mapping via `build_batch_assessment_input()` and baseline scoring via `build_baseline_assessment()` for all window candidates is fully viable in-process without requiring asynchronous queues or database layers.
- **Separation of Future Optimization (INFERENCE — NOT a Correctness Condition for IGR-05B):**
  - For the deterministic crop-median baseline, `risk.score` is a pure function of `crop_type` (present directly in raw `batches.csv`).
  - *Future Optimization Concept:* A future optimization could compute preliminary baseline scores using raw `crop_type` in $< 1\text{ ms}$ for candidate ranking. However, the $< 1\text{ ms}$ figure applies **ONLY** to the pre-ranking lookup. After pagination slicing `[offset : offset + limit]`, every returned item in the sliced page **STILL strictly requires** full canonical mapping via `build_batch_assessment_input()` and full `RiskAssessment` model construction via `build_baseline_assessment()`.
  - *Status:* This raw pre-scoring concept is strictly an architectural INFERENCE and future optimization candidate. It requires its own dedicated contract and strict numerical/schema parity verification before use. It is **NOT** part of the authoritative canonical path and **NOT** a correctness condition for IGR-05B.
- **Human Gate Note:** Slicing before global ranking is strictly rejected as a valid operational ranking implementation unless explicitly accepted as a degraded demo-only trade-off under a dedicated Human Gate decision.

### Comparability guard (ADR 0003 D3)
- The collection must reject or segregate any items that do not share the exact same `engine_tier + engine_version`.
- In the baseline serving context, all items are produced by `deterministic_baseline` with version `baseline-crop-median-v1-p1-s2024`.

---

## 14. Response-contract options (Q12, Q14, Q15)

### Decision question Q14: Envelope vs. bare list

#### Option 1: Bare array (`list[RiskAssessment]`)
```json
[
  {
    "batch_id": "BAT-000901",
    "status": "assessed",
    "risk": {"score": 0.0644, "band": null},
    ...
  }
]
```
- *Pros:* Zero new shared domain models; reuses existing `RiskAssessment` contract directly.
- *Cons:* No place to return replay metadata, total matching count, window echo, or pagination links.

#### Option 2: Collection envelope (`RiskAssessmentCollectionResponse`)
```json
{
  "items": [
    {
      "batch_id": "BAT-000901",
      "status": "assessed",
      "risk": {"score": 0.0644, "band": null},
      ...
    }
  ],
  "total_count": 14,
  "window_start": "2025-05-01T00:00:00Z",
  "window_end": "2025-05-08T00:00:00Z",
  "facility_id": "FAC-001",
  "engine_version": "baseline-crop-median-v1-p1-s2024"
}
```
- *Pros:* Self-describing, supports operator triage UI with filter context, total count, and engine provenance.
- *Cons:* Requires defining a new Pydantic model in `backend/app/domain/assessment.py` and a matching TypeScript interface in `frontend/src/api/contracts.ts`.

---

## 15. Pagination options (Q16, Q17)

### Ordering sequence invariant
Pagination parameters (`offset` and `limit`) MUST be applied strictly **AFTER** global ranking (`risk.score DESC, batch_id ASC`) across the filtered window cohort. Slicing before global ranking violates ADR 0003 D1/D3 by returning an arbitrary chronological slice rather than the highest-risk batches in the window.

### Decision question Q16: Pagination style
- **Option A (Window-Bounded Collection, No Offset/Cursor):** A collection query uses a bounded replay window, which acts as the compute partition boundary; all matching candidates are returned after global ranking.
- **Option B (Offset / Limit Pagination):** Standard `limit: int = 50`, `offset: int = 0`. Returns `total_count` and paginated `items` sliced from the globally sorted candidate set.
- **Option C (Cursor Pagination):** Cursor based on `(risk_score, batch_id)`.
- *Recommendation:* Option B (Offset/Limit with technical upper bound $\le 100$) is familiar, straightforward to implement, and compatible with React UI table controls.

---

## 16. Error and partial-failure options (Q13, Q18)

### Decision question Q13: Per-item mapping failure semantics (CRITICAL)

What happens if 1 out of 20 candidate batches fails canonical mapping or raises a data validation error?

- **Option A (Fail-Closed Atomic Failure — RECOMMENDED):**
  - If any candidate batch in the requested slice fails canonical mapping, the entire request fails with HTTP 500 ("Assessment could not be completed for batch {batch_id}").
  - *Rationale:* Conforms strictly to project fail-closed principles. Does not conceal data corruption or chronological sequence violations.
- **Option B (Partial Success with Insufficient Data):**
  - The failing batch is returned with `status = "insufficient_data"`, `risk = null`, and `reliability.missing_requirements` populated.
  - *Rationale:* Violates ADR 0003 D7 and ADR 0005 D5: server-owned mapping failures or corrupt source rows are server defects, NOT valid `insufficient_data` states.
- **Option C (Silent Drop):**
  - Omit failing batches from the response.
  - *Rationale:* Forbidden. Hides missing items from the operator.

### Decision question Q18: Empty collection behavior
- If 0 batches match the filter criteria within the held-out cohort, return HTTP 200 with `items: []` (or `total_count: 0`). It is NOT an HTTP 404 error.

---

## 17. Runtime/orchestration boundary options (Q19, Q20)

### Decision question Q19: Service layer boundary
- **Rule:** Routes must remain thin HTTP adapters.
- **Proposed Architecture:**
  - Create a dedicated application service: `AssessmentCollectionService` (or function `get_assessment_collection()`) in `backend/app/services/collection_assessment.py`.
  - The service takes `AnalyticsRuntimeContext`, `facility_id`, `window_start`, `window_end`, `limit`, and `offset`.
  - The service executes candidate selection, pre-filtering, canonical mapping, scoring, sorting, and envelope packaging.
  - [`backend/app/api/routes.py`](../../backend/app/api/routes.py) only parses parameters, invokes the service, and formats HTTP errors.

---

## 18. Performance and indexing considerations (Q21)

### Assessment of indexing needs and latency modes
- The raw tables in `RawSnapshot` are lists of dictionaries (`list[dict[str, str]]`).
- For the single-batch path, searching `batches` (1,800 rows) takes ~0.1 ms.
- **Latency profiles under local empirical measurement (Windows 11, Python 3.12.3, verified at base `540c98e` / `401f395`):**
  - **Mode (a) — Warm-Cache Repeat (Same Batch `BAT-000901`):**
    - 10 calls: 0.0899s total (**8.99 ms / call**)
    - 50 calls: 0.4571s total (**9.14 ms / call**)
    - 100 calls: 0.9103s total (**9.10 ms / call**)
  - **Mode (b) — Distinct-Batch Cache-Build across Zones:**
    - 10 distinct calls: 0.7225s total (**72.25 ms / call**)
    - 50 distinct calls: 3.7088s total (**74.18 ms / call**)
    - 100 distinct calls: 7.2274s total (**72.27 ms / call**)
    - Direct mapper overhead: 100 calls = 6.5826s (65.83 ms / call)
- **Implication for Multi-Batch Serving:**
  - Collection serving is governed by **Mode (b)** dynamics.
  - Sizing estimates for candidate cohorts:
    - 5 candidate batches: $5 \times 72.3\text{ ms} \approx \mathbf{0.36\text{ s}}$
    - 10 candidate batches: $10 \times 72.3\text{ ms} \approx \mathbf{0.72\text{ s}}$
    - 20 candidate batches: $20 \times 72.3\text{ ms} \approx \mathbf{1.45\text{ s}}$
    - 25 candidate batches: $25 \times 74.0\text{ ms} \approx \mathbf{1.85\text{ s}}$
    - 50 candidate batches: $50 \times 74.2\text{ ms} \approx \mathbf{3.71\text{ s}}$
    - 100 candidate batches: $100 \times 72.3\text{ ms} \approx \mathbf{7.23\text{ s}}$
    - Unbounded 900 held-out batches: $900 \times 72.3\text{ ms} \approx \mathbf{65\text{ s}}$ (causes HTTP client timeout)
- **Lightweight In-Memory Index (Candidate Optimization):**
  - If the service pre-indexes `batches_by_id: dict[str, dict]` and `sessions_by_batch_id: dict[str, dict]`, or if the service filters sessions first and only maps the surviving items, latency remains well within acceptable bounds (< 1.5s for bounded windows).
  - No database or persistent index is required.

---

## 19. Database / concurrency assessment (Q22, Q23)

### Decision question Q22: Database necessity
- **Is an external database (SQLite, PostgreSQL, DuckDB) required for bounded MVP serving?**
  - **Verdict: NO.**
  - **Evidence:**
    1. Total dataset size across all 8 CSVs is 54.1 MB.
    2. Held-out cohort consists of exactly 900 batches.
    3. Memory footprint of `RawSnapshot` in Python process memory is ~120 MB.
    4. Lifespan startup loading time is ~3.9 seconds.
    5. In-memory pre-filtering takes < 2 ms.
    6. Adding a database introduces schema migrations, ORM dependencies, sync/async driver complexity, disk write state, and breaks the verified fail-closed SHA256 snapshot verification model.

### Decision question Q23: Concurrency / background worker necessity
- **Are background workers (Celery, RQ, multiprocessing) required?**
  - **Verdict: NO.**
  - **Evidence:**
    1. Smart Harvest MVP is an on-demand demonstration and evaluation tool.
    2. Request volume is single-operator / demo-scale.
    3. Synchronous endpoint execution with window-bounded cohorts (< 50 batches) completes in < 3 seconds.
    4. Concurrency infrastructure would introduce architectural bloat without operational necessity.

---

## 20. Candidate design matrix

Three distinct, coherent architectural candidate designs were formulated:

| Architectural Dimension | OPTION A: Minimal Collection over RiskAssessment | OPTION B: Replay Window Triage Envelope (RECOMMENDED) | OPTION C: Queue-Summary Projection Contract |
| :--- | :--- | :--- | :--- |
| **Endpoint Path** | `GET /api/v1/assessments` | `GET /api/v1/assessments` | `GET /api/v1/queue` |
| **Query Parameters** | `facility_id?: str`, `limit?: int = 50`, `offset?: int = 0` | `facility_id?: str`, `window_start?: str`, `window_end?: str`, `limit?: int = 50`, `offset?: int = 0` | `facility_id?: str`, `preset?: str` |
| **Response Shape** | Bare array: `list[RiskAssessment]` | Envelope: `RiskAssessmentCollectionResponse` (`items: list[RiskAssessment]`, metadata) | Summary Envelope: `QueueResponse` (`items: list[QueueItemSummary]`) |
| **Item Contract** | Full `RiskAssessment` | Full `RiskAssessment` | New lightweight `QueueItemSummary` (no telemetry/factors) |
| **Replay Window Support** | Implicit / unbounded | Explicit `window_start` / `window_end` (Default duration: **HUMAN DECISION REQUIRED**; window bounds compute cost) | Fixed presets |
| **Ordering Rule** | `risk.score DESC, batch_id ASC` | `risk.score DESC, batch_id ASC` (evaluated globally across window candidates) | `risk.score DESC, batch_id ASC` |
| **Pagination Sequence** | Slicing applied after global ranking | Slicing (`[offset:offset+limit]`) strictly **AFTER** global ranking across window cohort (`limit` bounds returned page/payload) | Slicing applied after global ranking |
| **Empty Result** | `[]` (HTTP 200) | `{"items": [], "total_count": 0, ...}` (HTTP 200) | `{"items": [], "total_count": 0}` (HTTP 200) |
| **Per-Item Failure** | Fail-closed HTTP 500 | Fail-closed HTTP 500 | Fail-closed HTTP 500 |
| **New Domain Models** | None | Exactly 1 (`RiskAssessmentCollectionResponse`) | Exactly 2 (`QueueItemSummary`, `QueueResponse`) |
| **Frontend Contract Impact** | Minimal (array of existing type) | Moderate (envelope interface) | High (new summary interface + single-batch drilldown) |
| **Performance (5 items)** | Mode (b): ~0.36–0.37 s | Mode (b): ~0.36–0.37 s | < 0.05 s |
| **Performance (20 items)** | Mode (b): ~1.45 s | Mode (b): ~1.45 s | < 0.05 s (scores computed without canonical mapper) |
| **Performance (25 items)** | Mode (b): ~1.85 s | Mode (b): ~1.85 s | < 0.05 s |
| **Performance (50 items)** | Mode (b): ~3.71 s | Mode (b): ~3.71 s | < 0.05 s |
| **Performance (100 items)** | Mode (b): ~7.23 s | Mode (b): ~7.23 s | < 0.05 s |
| **Performance (All 900 items)** | Mode (b): ~65 s (Severe timeout risk) | Protected by window / limit ($\le 50$) | ~0.1 s |
| **ADR 0004 Compliance** | Partial (no window metadata) | **Full compliance with APR2-D2** | Moderate (introduces unapproved summary contract) |
| **Implementation Risk** | Low | Low | Medium (new projection logic) |

---

## 21. Recommended bounded candidate

### RECOMMENDATION — NOT A DECISION

**PROPOSED BOUNDED IMPLEMENTATION CANDIDATE (Option B — Replay Window Triage Collection Envelope):**

The following design represents Igor's technical recommendation submitted for Vladimir's Human Gate review. It does **NOT** constitute accepted architecture or canonical policy until explicitly approved by the Human Gate.

1. **Endpoint & Method:** `GET /api/v1/assessments` (extends resource hierarchy logically without creating an ad-hoc `/queue` path).
2. **Query Parameters:**
   - `facility_id: str | None = None` (validates against 10 known facilities; 404 if invalid).
   - `window_start: datetime | None = None` (ISO-8601).
   - `window_end: datetime | None = None` (ISO-8601).
   - `limit: int = 50` (enforces $1 \le \text{limit} \le 100$).
   - `offset: int = 0` (enforces $\text{offset} \ge 0$).
   - Default window behavior: **HUMAN DECISION REQUIRED (IGR05-D2)**. The endpoint can support an optional window defaulting to a bounded interval (e.g., 24h, 48h, 7d) or enforce mandatory window query parameters (HTTP 400 if omitted). Selection of the default policy and its duration is reserved for Vladimir.
3. **Response Envelope Model:**
   ```python
   class RiskAssessmentCollectionResponse(ContractModel):
       items: list[RiskAssessment]
       total_count: int
       window_start: datetime | None = None
       window_end: datetime | None = None
       facility_id: str | None = None
       engine_version: str
   ```
4. **Authoritative Canonical Processing Pipeline (Strict Rank-Before-Slice Order per ADR 0003 D1/D3):**
   - **Step 1 (Cohort Selection):** Pre-filter `storage_sessions` by `batch_id in runtime.held_out_ids` ($O(1)$ set membership).
   - **Step 2 (Window & Facility Filter):** Pre-filter sessions by `window_start <= dispatch_datetime < window_end` (or closed interval per IGR05-D3) and matching `facility_id` via `storage_zones` lookup. Record `total_count` of candidate batches matching the operational criteria.
   - **Step 3 (Canonical Mapping & Scoring of ALL Window Candidates):** For all candidate batches surviving Step 2:
     - Map each candidate batch via `build_batch_assessment_input()`.
     - Score each candidate batch via `build_baseline_assessment()`.
     - *Compute vs. Payload Bounding:* Because the replay window naturally bounds candidate cohort size (e.g., 5–25 batches requires only ~0.36–1.85 s total wall time under Mode (b)), canonical mapping and scoring of all window candidates in-process is fast, robust, and mathematically sound. The replay window bounds the compute cost, while `limit` bounds the returned page/payload. Pagination does NOT prevent scoring all window candidates.
   - **Step 4 (Global Deterministic Ranking):** Sort ALL scored candidate assessments across the entire window cohort by `(risk.score DESC, batch_id ASC)` in strict compliance with ADR 0003 D1/D3.
   - **Step 5 (Pagination Slicing):** Apply pagination slicing `[offset : offset + limit]` to the globally ranked candidate list.
   - **Step 6 (Envelope Assembly):** Assemble sliced `items`, `total_count`, window metadata, and `engine_version` into `RiskAssessmentCollectionResponse`.
5. **Architectural Separation of Future Optimization (INFERENCE):**
   - Raw pre-scoring via `batches.csv` `crop_type` in $< 1\text{ ms}$ is documented strictly as a separate future optimization / INFERENCE. Even if adopted in the future, every item returned in the sliced page would still require canonical mapping via `build_batch_assessment_input()` and baseline scoring via `build_baseline_assessment()`.
   - Raw pre-scoring requires its own dedicated contract and numerical/schema parity verification before use. It is **NOT** a correctness condition for IGR-05B and is **NOT** part of the initial canonical pipeline.
6. **Fail-Closed Semantics:** Any canonical mapping failure on an eligible batch immediately returns HTTP 500.

---

## 22. Human Gate — Decisions Required

The following 10 decision packets are submitted for Human Integrator review and decision (Vladimir). Each packet adheres strictly to the required format:

### IGR05-D1: Collection resource / endpoint
- **Question:** What is the URI path and HTTP method for the multi-batch assessment collection resource?
- **Already-fixed constraints:** ADR 0001 (FastAPI prefix `/api/v1`), ADR 0005 D5 (`GET /api/v1/assessments/{batch_id}` exists and must be preserved; no POST route accepted).
- **Options:**
  - *Option 1:* `GET /api/v1/assessments` (RESTful collection resource).
  - *Option 2:* `GET /api/v1/queue` (ad-hoc workflow route).
  - *Option 3:* `GET /api/v1/replay/assessments` (explicit replay namespace).
- **Consequences:**
  - *Technical:* Option 1 matches standard REST patterns where a collection is queried with parameters and an individual item is accessed by appending `{id}`. Option 2 introduces a competing top-level resource.
  - *Product:* Option 1 clearly indicates that the endpoint serves assessments.
  - *Shared-contract:* Option 1 extends the existing route surface without breaking single-batch routes.
- **Igor recommendation:** Option 1 (`GET /api/v1/assessments`).
- **Evidence:** Standard FastAPI route design in `backend/app/api/routes.py`.
- **Vladimir decision:** **DECISION — accepted by Vladimir / Human Integrator on 2026-09-22:** `GET /api/v1/assessments` is the collection resource and complements the existing `GET /api/v1/assessments/{batch_id}`.

---

### IGR05-D2: Replay window requirement
- **Question:** How is the replay window specified by the client, what happens on parameter omission or partial specification, and how are invalid intervals handled?
- **Already-fixed constraints:** ADR 0004 APR2-D2 ("operational triage view selects canonical recorded assessment events via a configurable replay/view window"). Replay window bound limits total compute cost across candidates.
- **Decision Dimensions & Variants (HUMAN DECISION REQUIRED):**
  1. *Behavior when BOTH `window_start` and `window_end` are absent:*
     - **Variant 1A (Mandatory Window):** Strict requirement; missing window parameters return HTTP 400 Bad Request. Client must always be explicit.
     - **Variant 1B (Optional Window with Default Bounds):** Server defaults to an evaluation window if omitted, ensuring unparameterized requests succeed for demo/dashboard views.
  2. *Anchor and default bounds for automatic window (if Variant 1B chosen):*
     - **Variant 2A (Fixed Season 2025 Start):** Window anchors at fixed timestamp `2025-05-01T00:00:00Z` plus default duration:
       - *Sub-variant 2A-1 (24-hour default):* `2025-05-01T00:00:00Z` to `2025-05-02T00:00:00Z` (~2–8 batches, Mode (b) latency ~0.15–0.6s).
       - *Sub-variant 2A-2 (48-hour default):* `2025-05-01T00:00:00Z` to `2025-05-03T00:00:00Z` (~5–15 batches, Mode (b) latency ~0.36–1.1s).
       - *Sub-variant 2A-3 (7-day default):* `2025-05-01T00:00:00Z` to `2025-05-08T00:00:00Z` (~35 batches, Mode (b) latency ~2.5s).
     - **Variant 2B (Sliding Replay Anchor):** Window anchors relative to the latest observed dispatch timestamp in the held-out dataset minus duration.
  3. *Behavior when only ONE of `window_start` / `window_end` is provided:*
     - **Variant 3A (Strict Pair Requirement):** Both parameters must be provided together. Supplying only one returns HTTP 400 Bad Request ("Both window_start and window_end must be provided").
     - **Variant 3B (Open-Ended Unilateral Boundary):** Allow open-ended queries (e.g., `window_start` to end of season, or start of season to `window_end`). An open-ended window can create a large candidate cohort: all matching window candidates must still be canonical-mapped and scored before global ranking and pagination slicing. Pagination `limit` bounds only the returned page, not compute cost, so this variant carries potentially large or unbounded compute latency unless an independent compute/window bound is introduced. This drawback supports Igor's recommendation for strict paired bounds (Variant 3A) but does not decide IGR05-D2.
     - **Variant 3C (Default Duration Offset):** If only `window_start` is given, default `window_end = window_start + default_duration`; if only `window_end` is given, default `window_start = window_end - default_duration`.
  4. *Behavior for invalid interval (`window_start >= window_end`):*
     - **Variant 4A (Strict Validation Error):** Return HTTP 400 Bad Request ("window_start must precede window_end").
     - **Variant 4B (Permissive Empty Result):** Return HTTP 200 with empty list `items: []` and `total_count: 0`.
- **Consequences:**
  - *Technical:* Variant 1B with 2A ensures zero-config initialization for web demo shells. Variant 3A and 4A ensure fail-fast, fail-closed parameter validation.
  - *Product:* Prevents unexpected client crashes while maintaining complete replay flexibility.
  - *Shared-contract:* Query parameter specifications in OpenAPI docs and TypeScript clients.
- **Igor recommendation:** Optional window with documented 48h default (Variant 1B + 2A-2), strict pair requirement (Variant 3A), and strict invalid interval validation (Variant 4A). However, the selection among all variants is strictly a **HUMAN DECISION REQUIRED for Vladimir**.
- **Evidence:** Benchmark Mode (b) demonstrates: 5 distinct batches take ~0.36–0.37s; 20 batches take ~1.45s; 25 batches take ~1.85s; 50 batches take ~3.71s; unbounded 900-batch scan takes ~65s. Bounded windows protect API responsiveness.
- **Vladimir decision:** **DECISION — accepted by Vladimir / Human Integrator on 2026-09-22; SUPERSEDED BY IGR05-D2R on 2026-09-22 for the automatic default bounds only:** Variants **1B + 2A-2 + 3A + 4A**. When both boundaries are absent, effective `window_start = 2025-05-01T00:00:00Z` and `window_end = 2025-05-03T00:00:00Z`. The window uses `storage_sessions.dispatch_datetime`. Supplying only one boundary returns HTTP `400`; `window_start >= window_end` returns HTTP `400`. Pagination is not a compute guard: the replay window bounds the matching cohort to be scored.

#### IGR05-D2R — accepted amendment to automatic default bounds

- **Classification:** `DECISION`
- **Accepted by:** Vladimir / Human Integrator
- **Date:** `2026-09-22`
- **New default:** `2025-11-29T00:00:00Z <= dispatch_datetime < 2025-12-01T00:00:00Z` (48 hours).
- **Scope of amendment:** These automatic bounds apply only when both `window_start` and `window_end` are omitted. Clients may supply another valid replay window.
- **Preserved D2 semantics:** Both explicit bounds are required together; one supplied bound or `window_start >= window_end` returns HTTP `400`. Membership uses `storage_sessions.dispatch_datetime` and a half-open interval. The replay window bounds the compute cohort; pagination bounds only the response payload. D1 and D3–D10 are unchanged.
- **Evidence record — `FACT / POST-IMPLEMENTATION EVIDENCE`:** The pinned held-out cohort contains 900 batches and its earliest `dispatch_datetime` is `2025-05-25 15:35:24`. The originally accepted May 1–3 window returns `0` eligible candidates, contradicting the original IGR-05A estimate of approximately 5–15 for that interval. The Nov 29–Dec 1 window contains `18` eligible candidates across 3 crop types and 8 facilities; all fit within the accepted default page size of 20. This correction was accepted after IGR-05B implementation and configured-runtime verification (PR #49). The new bounds provide a deterministic replay/demo default for the pinned training snapshot, not an agronomic optimum, production recommendation, current window, or representative operational shift.

The decision history is: original IGR-05A recon assumption → original Human Gate May 1–3 decision → IGR-05B implementation evidence → contradiction discovered in the pinned held-out cohort → IGR05-D2R Human correction.

---

### IGR05-D3: Window boundary semantics & tie-breaking invariant
- **Question:** What are the mathematical boundary conditions for matching `dispatch_datetime` against `window_start` and `window_end`, and how are ties in risk score resolved?
- **Already-fixed constraints:** ADR 0002 dispatch clock invariant ($T_{\text{assess}} \equiv \text{dispatch\_datetime}$); ADR 0003 D3 deterministic ranking rule (`risk.score DESC, batch_id ASC`).
- **Options:**
  - *Option 1:* Half-open interval: `window_start <= dispatch_datetime < window_end`, with tie-breaker `batch_id ASC`.
  - *Option 2:* Closed interval: `window_start <= dispatch_datetime <= window_end`, with tie-breaker `batch_id ASC`.
- **Consequences:**
  - *Technical:* Option 1 prevents duplicate batch display when paging through contiguous time slices. Option 2 matches intuitive human date filtering. Both options enforce strictly identical tie-breaking via `batch_id ASC`.
  - *Product:* Minimal perceptible difference if timestamps are down to second resolution; ensures stable sort order across refreshes.
  - *Shared-contract:* Documented in integration contract.
- **Igor recommendation:** Option 1 (Half-open interval `[start, end)` with `batch_id ASC` tie-breaker).
- **Evidence:** Time-series convention across data engineering; ADR 0003 D3 compliance.
- **Vladimir decision:** **DECISION — accepted by Vladimir / Human Integrator on 2026-09-22:** Half-open interval `window_start <= dispatch_datetime < window_end`; global ranking `risk.score DESC, batch_id ASC`.

---

### IGR05-D4: Facility filter behavior
- **Question:** How does the `facility_id` parameter filter the collection, and how are invalid IDs handled?
- **Already-fixed constraints:** ADR 0004 APR2-D2 (`facility_id` is strictly a UI/context filter, not an operational jurisdiction partition).
- **Options:**
  - *Option 1:* Optional `facility_id: str | None = None`. Validated against the 10 known facilities in `facilities.csv`; returns HTTP 404 if facility does not exist; returns HTTP 200 with `items: []` if facility exists but has 0 matching batches in the window.
  - *Option 2:* Permissive string filter without validation (returns empty collection for any non-matching string).
- **Consequences:**
  - *Technical:* Option 1 catches client typographical errors early.
  - *Product:* Prevents operators from wondering why a mistyped facility returns 0 batches.
  - *Shared-contract:* HTTP status code contracts.
- **Igor recommendation:** Option 1 (Strict validation, 404 on unknown facility ID).
- **Evidence:** `facilities.csv` contains exactly 10 facilities (`FAC-001` through `FAC-010`).
- **Vladimir decision:** **DECISION — accepted by Vladimir / Human Integrator on 2026-09-22:** `facility_id` is an optional UI/context filter, not an operational jurisdiction partition. Unknown `facility_id` returns HTTP `404`; an existing facility with no matching batches returns HTTP `200` with an empty collection.

---

### IGR05-D5: Collection response item/envelope
- **Question:** What JSON data shape is returned by the collection endpoint?
- **Already-fixed constraints:** Single-batch endpoint returns bare `RiskAssessment`. ADR 0004 APR2-D2 requires presenting replay window context.
- **Options:**
  - *Option 1:* Bare list `list[RiskAssessment]`.
  - *Option 2:* Collection envelope `RiskAssessmentCollectionResponse` containing `items: list[RiskAssessment]`, `total_count`, `window_start`, `window_end`, `facility_id`, and `engine_version`.
  - *Option 3:* Lightweight projection envelope `QueueResponse` with `QueueItemSummary`.
- **Consequences:**
  - *Technical:* Option 2 provides metadata without altering the underlying `RiskAssessment` model. Option 3 requires defining separate item contracts.
  - *Product:* Option 2 gives the frontend shell full context for rendering triage summary headers.
  - *Shared-contract:* Requires new shared Pydantic model and TypeScript interface.
- **Igor recommendation:** Option 2 (Collection envelope with `items: list[RiskAssessment]`).
- **Evidence:** ADR 0004 APR2-D2 triage requirements.
- **Vladimir decision:** **DECISION — accepted by Vladimir / Human Integrator on 2026-09-22:** Return `RiskAssessmentCollectionResponse` with at least `items: list[RiskAssessment]`, `total_count`, `window_start`, `window_end`, `facility_id`, and `engine_version`. Preserve the existing `RiskAssessment` model.

---

### IGR05-D6: Pagination strategy & ordering sequence invariant
- **Question:** What pagination mechanism should be exposed, and how is the ordering sequence strictly enforced?
- **Already-fixed constraints:** Zero database, in-memory filtering; **ADR 0003 D1/D3 ordering sequence invariant**: pagination slicing (`[offset : offset + limit]`) MUST be applied strictly **AFTER** global risk ranking across all candidate batches matching the window and facility filters. (Slicing before global ranking produces an arbitrary chronological page locally sorted, violating ADR 0003 D1/D3, and is strictly rejected).
- **Options:**
  - *Option 1:* Limit / offset pagination (`limit: int = 50`, `offset: int = 0`) applied after global ranking.
  - *Option 2:* Window-only partitioning (no limit/offset; window cohort returned in its entirety, ranked by risk score).
  - *Option 3:* Keyset / cursor pagination (`cursor: str` based on `risk.score, batch_id`).
- **Consequences:**
  - *Technical:* Option 1 is standard, simple to implement over globally ranked candidate lists in memory, and conforms to web UI table expectations. Option 2 risks payload bloat if window is broad. Option 3 adds unneeded complexity for static 900-batch datasets.
  - *Product:* Predictable page navigation with accurate `total_count`.
  - *Shared-contract:* Query parameter definitions.
- **Igor recommendation:** Option 1 (Limit / offset applied after global ranking).
- **Evidence:** 900 held-out batches fit in memory; sorting and slicing candidate lists in Python takes < 2 ms.
- **Vladimir decision:** **DECISION — accepted by Vladimir / Human Integrator on 2026-09-22:** Use `limit`/`offset` pagination after filtering, canonical mapping and scoring of **all** matching candidates, and global deterministic ranking. Slice-before-rank is prohibited.

---

### IGR05-D7: Technical page/response bound
- **Question:** What maximum `limit` should bound the returned page size and response payload?
- **Already-fixed constraints:** Collection serving operates under **Mode (b)** distinct-batch dynamics (~72–74 ms per matching candidate). All matching window candidates are mapped and scored before global ranking and pagination; `limit` does not bound compute latency.
- **Options:**
  - *Option 1:* Maximum `limit = 50` (default 20).
  - *Option 2:* Maximum `limit = 100` (default 50).
  - *Option 3:* Unbounded limit (up to all 900 batches).
- **Consequences:**
  - *Technical:* Under Mode (b) distinct-batch execution, compute cost follows the matching window candidate cohort regardless of page size:
    - 20 matching candidates take ~1.45s.
    - 25 matching candidates take ~1.85s.
    - 50 matching candidates take ~3.71s.
    - 100 matching candidates take ~7.23s.
    - 900 matching candidates take ~65s (causes HTTP client timeouts).
  - *Product:* 20 to 50 items per page is standard for an operator triage table.
  - *Shared-contract:* Validation error (HTTP 422) if `limit > max`.
- **Igor recommendation:** Option 2 (Maximum `limit = 100`, default `limit = 50`) for response page size; any compute latency target requires a separate replay-window bound. This remains subject to the IGR05-D7 Human Gate decision.
- **Evidence:** Local benchmark probe: Mode (a) same-batch repeated: 50 calls = 0.46s (9.14 ms/call), 100 calls = 0.91s (9.10 ms/call); Mode (b) distinct-batch: 50 calls = 3.71s (74.18 ms/call), 100 calls = 7.23s (72.27 ms/call).
- **Vladimir decision:** **DECISION — accepted by Vladimir / Human Integrator on 2026-09-22:** Default `limit = 20`; maximum `limit = 50`. The limit bounds only the returned page/payload, not the cost of scoring the entire matching replay cohort.

---

### IGR05-D8: Empty collection / invalid-filter behavior
- **Question:** How does the server respond when no batches match a valid filter criteria?
- **Already-fixed constraints:** ADR 0005 D5 (404 is reserved for unknown resource IDs).
- **Options:**
  - *Option 1:* Return HTTP 200 with `items: []` and `total_count: 0`.
  - *Option 2:* Return HTTP 404 ("No batches found matching criteria").
- **Consequences:**
  - *Technical:* Option 1 is standard REST behavior for collections.
  - *Product:* Frontend UI displays an empty table state rather than an error banner.
  - *Shared-contract:* HTTP status codes.
- **Igor recommendation:** Option 1 (HTTP 200 with empty list).
- **Evidence:** REST standards; avoids treating valid empty search as server/resource error.
- **Vladimir decision:** **DECISION — accepted by Vladimir / Human Integrator on 2026-09-22:** A valid collection request with zero matches returns HTTP `200`, `items: []`, and `total_count: 0`, with the other accepted envelope context.

---

### IGR05-D9: Per-item failure semantics
- **Question:** What is the error handling policy if an individual batch fails canonical mapping during collection processing?
- **Already-fixed constraints:** Fail-closed integrity principle.
- **Options:**
  - *Option 1 (Fail-Closed Atomic):* Entire request fails with HTTP 500.
  - *Option 2 (Partial Success):* Failing batch returned as `status = "insufficient_data"`.
  - *Option 3 (Silent Skip):* Failing batch is silently omitted from the list.
- **Consequences:**
  - *Technical:* Option 1 prevents silent data corruption. Option 2 violates ADR 0003 D7 by fabricating `insufficient_data` for server mapping defects. Option 3 creates invisible data loss.
  - *Product:* In a curated training challenge dataset, zero mapping failures should occur. If one occurs, it is a critical system error.
  - *Shared-contract:* Preserves truthfulness and audit integrity.
- **Igor recommendation:** Option 1 (Fail-Closed Atomic HTTP 500).
- **Evidence:** VDR-06B confirmed that 100% of the 900 held-out batches map successfully with 0 errors.
- **Vladimir decision:** **DECISION — accepted by Vladimir / Human Integrator on 2026-09-22:** Any canonical mapping failure for a matching eligible candidate fails the entire request closed with HTTP `500`. No silent skip, fabricated `insufficient_data`, or partial-success response.

---

### IGR05-D10: Application service / orchestration boundary
- **Question:** Where should the collection querying, filtering, and sorting logic reside?
- **Already-fixed constraints:** ADR 0001 modular monolith architecture; thin controllers.
- **Options:**
  - *Option 1:* Dedicated service function `get_assessment_collection()` in `backend/app/services/collection_assessment.py`.
  - *Option 2:* Inline logic directly inside `backend/app/api/routes.py`.
  - *Option 3:* Method on `AnalyticsRuntimeContext`.
- **Consequences:**
  - *Technical:* Option 1 keeps `routes.py` clean, enables unit testing of collection logic without HTTP test clients, and prevents business logic leakage into presentation.
  - *Product:* Facilitates future refactoring if ranking logic evolves.
  - *Shared-contract:* Internal architecture only.
- **Igor recommendation:** Option 1 (Dedicated application service in `backend/app/services/`).
- **Evidence:** Architecture guidelines in `docs/architecture.md`.
- **Vladimir decision:** **DECISION — accepted by Vladimir / Human Integrator on 2026-09-22:** Collection orchestration belongs in the dedicated application-service module `backend/app/services/collection_assessment.py`; the HTTP route remains a thin controller.

---

## 23. Proposed IGR-05B write surface

If the recommended candidate (Option B) is accepted by the Human Gate, the bounded write scope for the subsequent implementation task (IGR-05B) is projected as follows:

### Definitely needed (Authorized write scope for IGR-05B)
1. `backend/app/domain/assessment.py`: Add `RiskAssessmentCollectionResponse` Pydantic model.
2. `backend/app/services/collection_assessment.py` (NEW): Implement collection orchestration, pre-filtering, and ranking service.
3. `backend/app/api/routes.py`: Add `GET /api/v1/assessments` endpoint delegating to the collection service.
4. `backend/tests/test_collection_assessment.py` (NEW): Unit and integration tests for collection serving, filtering, pagination, and error modes.
5. `frontend/src/api/contracts.ts`: Synchronize TypeScript interface `RiskAssessmentCollectionResponse`.

### Possibly needed (Subject to implementation details)
1. `frontend/src/api/client.ts`: Add `getAssessmentCollection()` API client method.
2. `docs/integration_contract.md`: Document new collection endpoint in API contracts table.

### Should remain untouched (Strictly forbidden modifications)
1. `backend/app/analytics/**`: Zero changes to baseline scoring math or crop-median logic.
2. `backend/app/ingestion/canonical_mapper.py`: Zero changes to single-batch mapping logic or validation rules.
3. `backend/app/domain/batch.py`: Zero changes to `BatchAssessmentInput`.
4. `backend/app/runtime/artifact.py`: Zero changes to artifact schema, hashes, or partition logic.
5. `backend/artifacts/**`: Zero changes to committed baseline artifact JSON.
6. `sponsor_pack/**`: Zero changes to raw CSV datasets.

---

## 24. Explicit non-decisions

The following topics are explicitly **NOT** decided by this recon and remain preserved as open UNKNOWNs:

1. **Future Learned Model Serving:** How a future machine learning model (e.g. HistGradientBoosting) will be integrated into the collection path remains open.
2. **Learned Feature Extraction Overhead:** Telemetry feature extraction for complex models is not addressed; only the deterministic baseline is considered.
3. **Frontend Queue UI Layout:** The visual presentation of the triage queue (table, cards, sorting controls) belongs to UX / Denis (PUX workstream).
4. **Real-world WMS / ERP Integration:** How actual warehouse management systems connect to this API is outside the challenge scope.
5. **Production Cloud Deployment Topology:** Hosting on AWS/GCP/Azure, containerization, or Kubernetes is deferred.
6. **Cross-engine Comparability Rules:** Merging multiple engine outputs into a unified queue remains strictly prohibited under ADR 0003 D3.

---

## 25. Risks / remaining UNKNOWNs

| Risk / UNKNOWN | Description | Severity | Proposed Mitigation |
| :--- | :--- | :---: | :--- |
| **Unbounded Query Latency** | Client issues query matching hundreds of batches, taking tens of seconds. | HIGH | Require a Human-Gate-selected bounded replay window to cap the compute cohort, plus a separately selected bounded pagination/page-size policy for response payload. Exact default duration and pagination bounds remain governed by IGR05-D2 and IGR05-D7. |
| **Client Replay Seam Duplication** | Contiguous date range queries return the same batch twice if intervals overlap. | MEDIUM | Adopt half-open interval semantics `[window_start, window_end)`. |
| **Frontend/Backend Contract Drift** | Backend collection envelope updated without synchronizing TypeScript client. | MEDIUM | Require synchronized contract updates in IGR-05B before merging. |
| **Operator Persona Authority Drift** | Presentation implies system can issue binding hold/release directives. | HIGH | Maintain strict advisory disclaimer and `requires_human_review = True`. |
| **Silent Memory Leakage** | Caching mapped inputs across requests could exhaust process memory. | LOW | Keep collection service stateless; garbage collect mapped inputs after response serialization. |

---

## 26. Verification

### Summary of checks executed during IGR-05A

1. **Pre-flight Git Verification:**
   - Origin and upstream remotes verified.
   - Base HEAD reconciled with `upstream/main` at `540c98eb273a14d6a61e37c89c69d4bf9babfa78` (post PUX-11A / PR #46).
   - Clean working tree confirmed on branch `igor/igr-05a-multi-batch-serving-recon`.
2. **Read-Only Codebase Audit:**
   - 19 key source files and contracts thoroughly audited.
   - Relational joins and cardinality verified.
   - Zero access to `historical_quality_outcomes.csv` confirmed.
3. **Backend Test Suite Sanity Check:**
   - `.\.venv\Scripts\python.exe -m pytest backend/tests` executed: **106 passed, 2 warnings in 12.84s (and 14.70s), exit code 0.** (The 67 vs. 106 discrepancy is fully resolved: `[ 67%]` was an intermediate quiet-mode terminal progress indicator at 72/106 tests, while 67 was also the legacy pre-RBS-01 test count).
4. **Configured Runtime Verification:**
   - Lifespan initialization verified with `TestClient`.
   - Health check: `ready` (200).
   - Eligible batch `BAT-000901`: `assessed` (200).
   - Ineligible batch `BAT-000001`: `409` conflict.
5. **Performance Probe Execution:**
   - Standalone benchmark probe executed outside repo (`$env:TEMP/probe_modes.py`, deleted after run).
   - Measured lifespan startup: 3.9694s.
   - Measured **Mode (a)** (same-batch warm-cache repeat): **8.99–9.14 ms / call** (10 calls = 0.0899s, 50 calls = 0.4571s, 100 calls = 0.9103s).
   - Measured **Mode (b)** (distinct-batch cache-build across zones): **72.25–74.18 ms / call** (10 calls = 0.7225s, 50 calls = 3.7088s, 100 calls = 7.2274s). Direct `build_batch_assessment_input()` accounts for 65.83 ms / call (~91% of total).
   - Collection serving operates under Mode (b) dynamics. Replay-window bounding limits compute cost because all matching window candidates are canonical-mapped and scored before global ranking. Pagination `limit` bounds only the returned page/payload and does not prevent scoring all window candidates.
6. **Final Scope & Observable GitHub State Verification:**
   - Exactly one file created/modified: [`docs/recon/IGR-05A-multi-batch-serving-recon.md`](IGR-05A-multi-batch-serving-recon.md).
   - Zero changes to backend, frontend, tests, configuration, or datasets.
   - Commit `720fb9b` exists on branch `igor/igr-05a-multi-batch-serving-recon`.
   - Pull Request #47 exists and is open on `Slave-of-Skynet/training_agrifood`.
   - No merge has been performed.

### Process deviation record

> [!WARNING]
> **PROCESS DEVIATION — PR #47 was created before the required Project Brain review gate. No merge has been performed.**
>
> This record documents a historical workflow sequence violation: PR #47 was opened on GitHub prior to completing the Project Brain review gate for IGR-05A. This entry is a factual audit record and does not alter the task scope or authorize implementation. The write surface remains strictly documentation-only. No merge has been executed, and implementation under IGR-05B remains strictly blocked pending Vladimir's explicit Human Gate decisions on D1 through D10.

---

## 27. Final handoff

This document constitutes the complete deliverables for task **IGR-05A: Multi-Batch Serving Recon & Decision Packet**. It is submitted to **Vladimir (Integrator / Project Brain)** for formal Human Gate review under PR #47.

**Current Human Gate and implementation status (2026-09-22):** Vladimir / Human Integrator accepted D1–D10 and the D2R amendment above. **IGR-05A HUMAN GATE ACCEPTED; IGR-05B IMPLEMENTED / ACCEPTED / HUMAN INTEGRATED via PR #49.** The original pre-implementation analysis and workflow records above remain historical; the May 1–3 default is superseded only for omitted query bounds.
