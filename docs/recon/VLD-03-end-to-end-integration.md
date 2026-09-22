# VLD-03 — End-to-End Integration and Behaviour Gate

**Date:** 2026-09-23

**Verdict:** **ACCEPTABLE** — evidence complete in this changeset; Human Integration, merge, deployment, release, and submission remain separate decisions.

**Evidence labels:** **REAL PRODUCT EVIDENCE** means the pinned sponsor snapshot and committed application were exercised; **SYNTHETIC FAULT-INJECTION EVIDENCE** means a temporary local stub was used only to test UI failure handling; **CODE/TEST EVIDENCE** means committed source or tests were inspected or executed.

## 1. Base / environment

- Repository: `Slave-of-Skynet/training_agrifood`; branch: `vladimir/vld-03-end-to-end-integration`.
- `main` was clean. `git pull --ff-only` fast-forwarded it from `d6b7df1` to the authoritative PR #52 merge commit `b88e81a700188d9dd7dc95d9be757a6b6b81f900`; the VLD-03 branch was created there. HEAD stayed at that SHA during this verification.
- Local Windows/PowerShell workspace; Python virtual environment `.venv`; frontend npm/Vite. Backend and frontend were served on `127.0.0.1:8000` and `127.0.0.1:5173`. Mode B used `sponsor_pack/data` and `backend/artifacts/baseline-crop-median-v1-p1-s2024.json` through process environment variables only.
- No application source, sponsor data, artifact, dependency, lockfile, schema, or runtime configuration was edited. The temporary fault stub was written under `%TEMP%`, stopped, and removed.

## 2. Paths inspected

**CODE/TEST EVIDENCE:** `backend/tests/test_ingestion_canonical.py`, `test_analytics_baseline.py`, `test_baseline_assessment.py`, `test_runtime_baseline.py`, `test_collection_assessment.py`, and `test_api.py`; `backend/app/ingestion/canonical_mapper.py`, `backend/app/runtime/context.py`, `backend/app/services/baseline_assessment.py`, `backend/app/services/collection_assessment.py`, and `backend/app/api/routes.py`; `frontend/src/api/client.ts`, `frontend/src/components/AssessmentQueue.tsx`, `frontend/src/components/AssessmentCard.tsx`, and `frontend/src/pages/HomePage.tsx`; ADRs 0002–0007, `docs/demo_runbook.md`, and `docs/integration_contract.md`.

The inspected chain is pinned raw snapshot → runtime validation and partition/artifact loading → raw tables → canonical mapper → crop-median baseline → `RiskAssessment` → collection sort and slicing → collection GET → queue → selected card. The collection service maps and scores the complete matching held-out cohort before sorting by `(-risk.score, batch_id)` and slicing. The frontend renders `collection.items` in received order, and passes a selected item to the card without refetching it.

## 3. Automated verification

**CODE/TEST EVIDENCE:** Commands were run from the repository root except npm commands, which ran in `frontend`.

| Command | Actual result |
| --- | --- |
| `.\.venv\Scripts\python -m pytest backend/tests` | Exit 0; **114 passed, 0 failed, 2 warnings in 21.13s**. Warnings: `StarletteDeprecationWarning` for TestClient/httpx and `DeprecationWarning` for the AnyIO BlockingPortal alias. |
| `.\.venv\Scripts\python -m pytest backend/tests/test_ingestion_canonical.py -q` | Exit 0; 26 test dots, `[100%]`; no warning or duration summary printed by this quiet invocation. |
| `npm ci` | Exit 0; added 26 packages, audited 27 packages in 6s, 0 vulnerabilities. |
| `npm run typecheck` | Exit 0; `tsc -b --pretty false`. |
| `npm run build` | Exit 0; Vite v8.3.0, 20 modules transformed, built in 514ms; generated `dist/index.html` and CSS/JS assets. |
| `git diff --check` | Exit 0 after documentation reconciliation. |

Existing focused tests cover crop-median determinism/fallback and unsupported null output semantics; runtime validation, no request-time fitting, training/held-out membership, and fail-closed startup; collection filtering, UTC+03 normalization, global ranking, pagination, and error contracts; and single-batch health/demo behavior. No duplicate implementation tests were added for this evidence task.

## 4. Input/leakage boundary evidence

**CODE/TEST EVIDENCE:** `test_assessment_timestamp_is_dispatch_datetime` and the mapper set `T_assess = storage_sessions.dispatch_datetime`. `test_telemetry_interval_bounds` and `test_post_dispatch_telemetry_excluded` enforce `entry_datetime <= reading.timestamp <= dispatch_datetime`, inclusive. The implemented join is **batch → storage_session → zone → sensor_readings** through `zone_id`; it is not a direct batch-to-sensor join.

`test_arrival_quality_strictly_absent`, `test_realized_transit_fields_absent_from_canonical_model`, `test_historical_outcomes_absent_from_canonical_model`, and `test_canonical_model_rejects_extra_fields` cover the negative canonical contract. Arrival QC, actual departure/arrival, actual delay, cold-chain incident, realized transit temperature, historical commercial outcomes, and post-dispatch telemetry do not enter the canonical inference input. Planned logistics are a separate, conditionally eligible context.

`test_leakage_invariance_supplied_batch` mutates realized shipment fields, historical outcomes, and arrival QC for `BAT-000001`, then asserts identical canonical `model_dump()` output. `test_strong_leakage_invariance_synthetic_fixtures` additionally mutates post-dispatch telemetry and asserts the same canonical output. These are **canonical-mapping invariance** proofs for the tested fixtures; they do not establish a separate learned-model leakage or performance claim. The focused canonical suite executed successfully.

## 5. Runtime/startup evidence

**REAL PRODUCT EVIDENCE:** With the pinned data directory and artifact configured, `/api/v1/health` returned `{"status":"ok","service":"smart-harvest","analytics":"ready"}`. With both analytics settings removed, it returned `analytics: not_configured`. With the real data directory and a nonexistent artifact path, startup logged the missing artifact and returned `analytics: unavailable` while health stayed `status: ok`. Neither degraded state fabricated an assessment. All three states were exercised in separate backend processes; no invalid path was committed.

**CODE/TEST EVIDENCE:** `runtime/context.py` validates snapshot/artifact and training membership before publishing a ready context; failed initialization yields unavailable, and `get_runtime` returns 503. `test_runtime_baseline.py` covers missing/incompatible resources and training-only fitting.

## 6. API integration evidence

**REAL PRODUCT EVIDENCE:** The configured backend returned HTTP 200 for health, collection, and `BAT-000901`. Raw collection JSON (rather than PowerShell's local-time-converted `Invoke-RestMethod` datetime display) returned the exact bounds below.

| Route | Actual result |
| --- | --- |
| `GET /api/v1/health` | `{"status":"ok","service":"smart-harvest","analytics":"ready"}` |
| `GET /api/v1/assessments` | HTTP 200; `total_count=18`, 18 items; `window_start="2025-11-29T00:00:00+03:00"`, `window_end="2025-12-01T00:00:00+03:00"`; engine `baseline-crop-median-v1-p1-s2024`. |
| `GET /api/v1/assessments/BAT-000901` | HTTP 200; `status=assessed`, `risk.score=0.0644`, `provenance.simulation=true`, `deterioration_horizon=null`, `factors=[]`, `recommendation=null`. |

The first collection items were `BAT-000910`, `BAT-000950`, `BAT-001043`, `BAT-001196`, and `BAT-001213`, each with `risk.score=0.1476`. They form a tied cohort. The API and UI do not assign distinct ordinal risk levels to equal scores.

## 7. Frontend/network integration evidence

**REAL PRODUCT EVIDENCE:** Browser accessibility snapshots and Chrome DevTools Protocol network events were captured against the running Vite frontend and real backend.

- Initial load: completed `GET /api/v1/health → 200` and `GET /api/v1/assessments → 200`; 18 queue rows, replay bounds, engine version, and simulation notice visible. The detail area said “Select a batch to review”; no batch was preselected. React development mode issued an aborted duplicate health request; this did not create another completed collection result.
- Queue selection of `BAT-000910`: card showed `BAT-000910` and `0.1476`; the event interval contained **no** single-batch GET. Source inspection confirms `AssessmentQueue` maps `collection.items` directly with no client sort and calls `onSelect(assessment)`.
- Manual lookup of `BAT-000901`: network showed `GET /api/v1/assessments/BAT-000901 → 200`; card showed `BAT-000901` and `0.0644`.
- Tie presentation: first two rows and further tied rows showed `0.1476`; the queue explains tie/Batch ID ordering and displayed no rank number, “highest risk,” “critical,” or “urgent” distinction.
- Under network throttling, manual `BAT-000901` lookup started, then queue item `BAT-000950` was selected. The request emitted `net::ERR_ABORTED`; the card remained `BAT-000950`, and no visible `AbortError` appeared. The frontend also guards completion handlers with the aborted signal.

## 8. Negative-path matrix

Each actual-evidence cell refers to an executed browser/API observation, not an inferred pass.

| Scenario | Expected | Actual evidence |
| --- | --- | --- |
| Mode B healthy | Queue loads 18 | **REAL:** health/collection 200; 18 rows and matching bounds visible. |
| Queue selection | No single GET | **REAL:** `BAT-000910` card 0.1476; zero single-batch requests in selection event interval. |
| Manual lookup 200 | Assessment shown | **REAL:** `BAT-000901` GET 200 and card 0.0644. |
| Manual lookup 404 | Local error | **REAL:** `BAT-999999` GET 404, “Batch not found.”; queue remained. |
| Manual lookup 409 | Local eligibility error | **REAL:** `BAT-000001` GET 409, “not eligible for this assessment release”; queue remained. |
| Mode A not configured | No collection auto-load | **REAL:** health 200/not_configured; only health requested on reload; neutral queue-not-ready text. Explicit lookup got 503. |
| Configured runtime unavailable | No collection auto-load | **REAL:** health 200/unavailable with missing artifact; only health requested; neutral queue-not-ready text. |
| Backend unreachable | Unavailable / retry | **REAL:** Vite proxied health as 502; page showed “Unavailable” and “Try again”; no stale queue on reload. |
| Collection 200 empty | Neutral empty state | **SYNTHETIC:** health 200, collection 200; “No batches found in this replay window.” |
| Collection 500 | Queue error | **SYNTHETIC:** health 200, collection 500; “Priority queue could not be loaded.” and “Try again”. |
| Collection 503 | Runtime-unavailable queue error | **SYNTHETIC:** health 200, collection 503; “Analytics runtime unavailable.” and “Try again”. |
| Retry after failure | New request succeeds | **SYNTHETIC:** first collection 500; click produced a second collection GET 200 and `VLD03-STUB` row. |
| Stale manual lookup | Cannot overwrite queue selection | **REAL:** throttled single GET aborted, `BAT-000950` retained, no visible `AbortError`. |
| Mobile ~375px | Queue → detail → lookup → status | **REAL:** effective CSS viewport 372px; section positions followed that order; `scrollWidth=clientWidth=358`; visible Batch ID, score, button, and simulation notice. |

## 9. Fault-injection evidence

**SYNTHETIC FAULT-INJECTION EVIDENCE ONLY:** A temporary FastAPI fixture at `%TEMP%/vld03_fault_stub.py` occupied port 8000 while the real backend was stopped. Its health endpoint reported ready to exercise collection UI paths. The optional synthetic assessment carried `simulation=true` and the notice `SIMULATION / VLD-03 fault-injection fixture / not challenge evidence / not production deployment`. It was never challenge, business, scoring, or product-output evidence.

| Fixture scenario | Browser network | Visible result |
| --- | --- | --- |
| `empty` | health 200; collection 200 | Total 0 and neutral “No batches found in this replay window.” No API-error or safety claim. |
| `500` | health 200; collection 500 | “Priority queue could not be loaded.” and retry control; not rendered as empty. |
| `503` | health 200; collection 503 | “Analytics runtime unavailable.” and retry control; not rendered as empty. |
| `retry` | first collection 500; second collection 200 after button click | Error changed to one synthetic `VLD03-STUB` row with the fault-fixture simulation notice. Backend access log independently showed 500 then 200. |

Accessibility snapshots, network events, and browser screenshots were captured during each scenario in this task's live browser session. The stub was stopped and deleted; it does not appear in `git status`.

## 10. Mobile evidence

**REAL PRODUCT EVIDENCE:** A responsive browser screenshot was captured at an approximately 375px viewport (effective CSS `innerWidth=372`). With `BAT-000910` selected, DOM geometry placed Priority Queue, Batch Assessment, Evaluate Batch, and Available in that vertical order. The document's `scrollWidth` equaled `clientWidth` (358), so there was no horizontal page overflow. The browser accessibility snapshot exposed readable `BAT-000910`, score `0.1476`, the “View assessment” button, and both queue/card simulation notices. The button was clicked successfully at mobile width; operation did not depend on hover. The screenshot was captured in the live task output, not added as a third repository file.

## 11. Challenge outcome truth table

| Challenge outcome | Current implementation capability | Evidence and limit |
| --- | --- | --- |
| 1. Which batches are most at risk? | **SUPPORTED IN BOUNDED MVP FORM** | Deterministic loss-severity score, backend-ranked 18-item collection, tied-score semantics, real queue. This is severity prioritisation, not probability or guaranteed loss. |
| 2. When may quality deteriorate? | **NOT CURRENTLY ESTIMABLE** | Runtime `deterioration_horizon=null`; card says “Not estimable from supplied observations.” No timing prediction is claimed. |
| 3. Which factors contribute? | **NO VALIDATED PER-ASSESSMENT CONTRIBUTING FACTORS** | Baseline `factors=[]`. “How this score is computed” explains the formula, not causal factor attribution. |
| 4. What action should be prioritized? | **NO VALIDATED OPERATIONAL ACTION RECOMMENDATION** | Runtime `recommendation=null`; card neutrally says action recommendations are unavailable. Queue priority is not an intervention prescription. |

## 12. Claim audit

**CODE/TEST EVIDENCE:** `git grep -ni -E "probability|confidence|guarantee|highest risk|critical|urgent|dispatch now|hold|reject|re-cool|reduce loss|savings" -- frontend docs/demo_runbook.md` found `confidence_score` as a nullable TypeScript contract field, negative score qualifiers in the queue/card, and a Batch ID placeholder. No material positive probability/confidence/guarantee/action/savings claim was found in the frontend or runbook. `git grep -ni -E "Rank 1|Priority 1|#1" -- frontend` matched CSS hex colors ending in `#1...`; it found no ordinal ranking copy. The browser queue independently showed no ordinal ranks. These benign lexical matches are not contract failures.

## 13. Known limitations

- The baseline is a deterministic crop-conditioned historical median, with global training-median fallback for unseen crops. It is a training-challenge simulation, not a selected production learned model or deployment.
- The score supports bounded relative severity ordering only. Equal scores are ties; no calibrated probability, confidence percentage, risk band, guaranteed loss, or production alert threshold is available.
- Horizon, validated per-assessment factors, and operational recommendations are absent by accepted contract. This VLD-03 verdict does not turn those null/empty outputs into fulfilled challenge outcomes.
- Fault-injection screenshots and network traces were captured in the live task session and were intentionally not committed because the write contract allows only two documentation files. They can be reproduced using the scenario and status matrix above.

## 14. Shared-contract/config/dependency audit

| Audit item | Changed? |
| --- | --- |
| Backend implementation | No |
| Frontend implementation | No |
| API schema | No |
| Domain schema | No |
| Dependencies | No |
| Lockfile | No |
| Runtime config committed | No |
| Raw dataset | No |
| Baseline artifact | No |
| Scoring | No |
| Ranking | No |
| Accepted UX semantics | No |

Only `docs/recon/VLD-03-end-to-end-integration.md` and `docs/integration_contract.md` are repository writes. The latter corrects stale PUX-12A integration status and records this gate's evidence status; it does not alter FE-D1–FE-D6.

## 15. VLD-03 verdict

**ACCEPTABLE.** All required real integration, degraded, synthetic fault-injection, race, and mobile paths were exercised with no substantial contract violation observed. The PUX-12A browser evidence gap for empty/500/503/retry is closed. This is **EVIDENCE COMPLETE / ACCEPTABLE IN CHANGESET**, not Human Integrated. Merge, deployment, release, submission, learned-engine selection, and unsupported challenge outcomes require their own gates.
