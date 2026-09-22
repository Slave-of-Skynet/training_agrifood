# Integration Contract and Workstream Dependency Map

## Document status

- **Project:** SoS — Training Challenge #3 — AgriFood
- **Challenge:** Smart Harvest: Reduce Post-Harvest Losses
- **Human owner:** Vladimir — Integrator
- **Task:** VLD-01 — Build the Integration Contract and Workstream Dependency Map
- **Deliverable:** `docs/integration_contract.md`
- **Status:** VLD-01 ACCEPTED / INTEGRATED through [PR #6](https://github.com/Slave-of-Skynet/training_agrifood/pull/6).
- **Historical reconciliation:** VLD-R3 working update against accepted, integrated VLD-02A (ADR 0002, PR #16), VDR-03 (PR #18), and APR-01 (PR #17) at `9cff00ce177f32dc2562d3458e0659281438d4c3`, prepared for human review on 2026-09-20. This documentation reconciliation makes no new decision.
- **Historical reconciliation — VLD-02B:** At `aa5d40bee8368342e7a6b540278c26416cc89457`, VDR-04A was ACCEPTED / INTEGRATED through PR #20. Vladimir explicitly approved ADR 0003 D1–D10 on 2026-09-20 (integrated through PR #21).
- **Historical reconciliation — VLD-APR-HG1R (2026-09-21):** Human Integrator Vladimir explicitly accepted decisions APR2-D1–D6 via [ADR 0004](./decisions/0004-mvp-product-scope.md) on 2026-09-21. This reconciles canonical MVP product scope and UX boundary rules. Source documents [08_mvp_scope_decision_packet.md](./product_recon/08_mvp_scope_decision_packet.md) and [09_product_acceptance_traceability.md](./product_recon/09_product_acceptance_traceability.md) remain mixed research/spec artifacts; [PUX-08](./recon/PUX-08-data-ux-reconciliation.md) remains research/design recon (governed by ADR 0004 where applicable); runtime code and schemas remain unchanged.
- **Historical reconciliation — VLD-R5-HG1R / ADR 0005 (2026-09-22):** Human Integrator Vladimir explicitly accepted HG-R5 D1–D7 on 2026-09-22. [ADR 0005](./decisions/0005-runtime-baseline-serving.md) is authoritative. [VLD-R5](./recon/VLD-R5-runtime-assessment-path-recon.md) remains a reviewed RECON / DECISION PACKET; its recommendations are not wholesale canon. Reference base: `e8e14e3da7921a1d87f7bfc6e474f639ef87aa53`.
- **Historical reconciliation — VLD-R6 post-RBS-01 (2026-09-22):** Reconciled documentation at the PR #42 state (merge commit `794eac36b2deb7f244aeccc4ee2326100996edac`). Its statement that the frontend still consumed only synthetic demo describes that earlier state.
- **Current reconciliation — VLD-R8 / IGR05-D2R (2026-09-23):** PUX-11A integrated real single-batch frontend lookup via PR #46; IGR-05B implemented the backend collection route and shared collection response contract and was accepted / Human Integrated via PR #49. IGR05-D2R corrects only the omitted-bounds default to Nov 29–Dec 1 for the pinned snapshot. The frontend ranked collection queue and production deployment remain unimplemented.
- **Governing workstream:** [`docs/workstreams/vladimir-integration.md`](./workstreams/vladimir-integration.md)

---

# 1. Status, scope and source hierarchy

## 1.1. Purpose and scope

This document records the accepted VLD-01 integration contract and workstream dependency map for the SoS team in the Smart Harvest challenge. Its current-state entries include accepted VDR-04A evidence, human-approved ADR 0003 semantics, integrated PUX-08 UX reconciliation (DRAFT FOR REVIEW; governed by ADR 0004 where applicable), integrated IGR-02 raw ingestion and IGR-03 canonical `BatchAssessmentInput` mapping, and human-accepted ADR 0004 MVP product scope (decisions APR2-D1–D6 from APR-02F; source documents 08/09 remain mixed research/spec). IGR-04A fitting/scoring and IGR-04B internal assessment construction are implemented. ADR 0005 defines the initial serving architecture; RBS-01 implemented offline artifact generation, lifespan runtime loading, synchronized health states, and the single-batch route `GET /api/v1/assessments/{batch_id}` (PR #42). PUX-11A implemented frontend lookup through that real single-batch route (PR #46). IGR-05B implemented the backend collection route `GET /api/v1/assessments`, its shared response contract, and bounded ranked serving (PR #49); IGR05-D2R sets the default replay window to Nov 29–Dec 1 when both bounds are omitted. The frontend ranked multi-batch queue and learned models remain deferred. This reconciliation changes no public schema. It connects requirements, domain understanding, dataset reconnaissance, application implementation, evaluation, user experience, demonstration, and final presentation claims. The original pre-recon baseline remains part of project history; the current snapshot and evidence references are recorded in Section 8.

The scope of this document covers:

1. **Existing stable contracts:** Guarantees already implemented, tested, and accepted.
2. **Workstream producer → consumer dependencies:** Exact ownership, current accepted outputs, planned outputs, and downstream consumers across all team roles.
3. **Integration boundary matrix:** Producers, consumers, current contracts, unresolved questions, evidence requirements, and decision ownership across every major system boundary.
4. **UNKNOWN → evidence → decision triggers:** Explicit dependency links connecting canonical UNKNOWNs from [`docs/assumptions_unknowns.md`](./assumptions_unknowns.md) to evidence-producing tasks and decision gates.
5. **Shared-contract change triggers:** Mandatory human integration gates before modifying public or cross-cutting boundaries.
6. **Integration STOP conditions:** Explicit circumstances where downstream implementation or claims must halt.
7. **Current blocked / unblocked dependency state:** A concrete audit of what work may proceed immediately versus what is blocked awaiting evidence.
8. **Traceability rules:** The verified path from evidence to decision, shared contract, implementation, and evaluation.
9. **Current limitations:** Clear boundaries defining what this integration contract does not resolve.

### Explicit non-scope for VLD-01

This document intentionally does **not** decide, invent, or assume:

- A production `BatchInput` schema or raw-to-canonical mapping;
- Observed dataset quality, referential integrity, or row-level statistics;
- A risk calculation formula, heuristic, or scoring baseline;
- A machine learning model family, split design, target choice, or evaluation metric;
- Deterioration-horizon onset semantics or temporal estimation algorithms;
- Agronomic rules, crop-specific storage thresholds, or quality decline rates;
- Action-intervention efficacy or causal loss-reduction claims;
- Persistence technology, database engine, or ORM;
- Hosting, deployment platform, or cloud infrastructure;
- New API endpoints or breaking public contract modifications.

Those items were outside the original VLD-01 scope. ADR 0002 accepted canonical input semantics and IGR-03 implemented canonical mapping; ADR 0003 accepted bounded assessment/evaluation decisions. Remaining analytics scoring, engine runtime, and product choices still require their own evidence and gates.

---

## 1.2. Source authority and implementation-state authority

All workstream owners and automated agents must adhere to two explicitly separate authority rules:

### A. Challenge / requirement / decision authority

When determining requirements, specifications, challenge constraints, and architectural decisions, the following order of precedence is strictly authoritative:

1. **Current supplied challenge materials and newer explicit challenge clarification:** [`sponsor_pack/`](../sponsor_pack/), challenge briefs, and official sponsor Q&A or clarifications.
2. **Accepted SoS challenge-specific decisions and shared contracts:** [`docs/decisions/`](./decisions/), [`docs/architecture.md`](./architecture.md), [`docs/data_contract.md`](./data_contract.md), [`docs/domain_rules.md`](./domain_rules.md), [`docs/evaluation.md`](./evaluation.md), [`docs/demo_runbook.md`](./demo_runbook.md), [`docs/team_roles.md`](./team_roles.md).
3. **Challenge canon:** [`docs/challenge_canon.md`](./challenge_canon.md).
4. **General / process guidance:** General engineering guidelines, process runbooks, and team operating conventions.
5. **Current task / workstream notes:** Working notes, task descriptions, and checklists in [`docs/workstreams/`](./workstreams/).

**Core constraint:** Lower-level implementation convenience cannot override a higher-level challenge constraint.

**Simulated context notice:** Sponsor materials are a **SIMULATION / training package**. Statements in the sponsor pack must not be presented as empirical facts about a real GigaHack sponsor, real Moldovan agricultural businesses, or real commercial cold-storage operations.

### B. Current implementation-state authority

The committed application repository (`backend/`, `frontend/`) is authoritative for what is actually implemented, enforced, tested, or absent:

- Application code must **not** be used to infer challenge requirements.
- Conversely, roadmaps, task checklists, and design plans do **not** prove implementation exists if the committed code does not contain it.
- Application code is **not** classified as "Level 5" under the requirements hierarchy; it represents the ground truth of runtime software execution, not a source of business or challenge rules.
- When documentation claims an implementation exists that is not in the codebase, the committed codebase reflects the true state (e.g. SKELETON or UNIMPLEMENTED).

---

## 1.3. Standard claim classification

To prevent speculation from masquerading as verified capability, every technical assertion, documentation statement, and presentation claim must be classified into one of the following canonical categories:

| Classification | Meaning | Rule |
| --- | --- | --- |
| **FACT** | Directly supported by supplied challenge materials or empirically verified evidence. | Must cite an exact file path, commit, test result, or sponsor document. |
| **DECISION** | An explicit team engineering or product choice with recorded rationale. | Must cite an accepted ADR or canonical document under `docs/`. |
| **OBSERVED PRACTICE** | Behavior concretely observed in executed code or tests. | Must cite source code lines or test runs. |
| **INFERENCE** | A logical deduction from facts, but not yet empirically proven. | Must be labeled as an inference; cannot justify production claims. |
| **RECOMMENDATION** | A proposed future action or design option. | Cross-cutting recommendations affecting shared contracts, architecture, or product semantics require an integration decision gate (VLD-02). Local implementation recommendations within an already approved contract may be handled within their bounded task. |
| **UNKNOWN** | An unresolved question where data, evidence, or external clarity is lacking. | Local or task-specific UNKNOWNs remain within task recon evidence. Only cross-cutting project UNKNOWNs affecting shared decisions belong in canonical `docs/assumptions_unknowns.md`. Unresolved UNKNOWNs block only the downstream work that actually depends on them. |
| **SIMULATION** | Synthetic fixture or training simulation context. | Must be visibly labeled; must never be claimed as real operational data. |

---

# 2. Stable shared contracts and constraints

This section catalogs the foundational contracts, constraints, and architecture baselines governing the repository. To avoid conflating runtime code guarantees with project decisions or external challenge rules, every entry is explicitly categorized into one of four governance states:

1. **`IMPLEMENTED / ENFORCED CONTRACT`:** Codified, tested, and actively enforced in repository code (domain models, API routes, UI connection states).
2. **`ACCEPTED DECISION`:** Formal team architectural and methodology agreements recorded in accepted ADRs and documentation.
3. **`FIXED CHALLENGE / SPONSOR CONSTRAINT`:** Non-negotiable external invariants supplied by the training challenge specification ($T_{assess} = T_{dispatch}$).
4. **`DOCUMENTED BUT NOT YET IMPLEMENTED/ENFORCED`:** Specifications described in design documents or schemas but not yet implemented, executed, or verified in application code.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        React + TS Operator UI                          │
│     (HomePage.tsx, AssessmentCard.tsx, BackendStatus.tsx)              │
│     [IMPLEMENTED / ENFORCED CONTRACT]                                  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                             HTTP GET /api/v1/*
                             [IMPLEMENTED / ENFORCED CONTRACT]
                                     │
┌────────────────────────────────────▼───────────────────────────────────┐
│                        FastAPI + Pydantic API                          │
│     (/api/v1/health, /api/v1/demo/assessment)                          │
│     [IMPLEMENTED / ENFORCED CONTRACT]                                  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                           Enforces Domain Models
                                     │
┌────────────────────────────────────▼───────────────────────────────────┐
│                    Pydantic Contract: RiskAssessment                   │
│   - status: assessed | insufficient_data                               │
│   - risk: RiskEstimate (score ∈ [0,1]) | null                          │
│   - deterioration_horizon: DeteriorationHorizon | null                 │
│   - factors: list[AssessmentFactor]                                    │
│   - recommendation: Recommendation | null                              │
│   - reliability: Reliability                                           │
│   - provenance: Provenance                                             │
│   [IMPLEMENTED / ENFORCED CONTRACT on synthetic fixture]               │
└────────────────────────────────────────────────────────────────────────┘
```

## 2.1. Detailed contract inventory

**Public contract extension rule:** For public and shared contracts, even an apparently additive optional field or enum extension is not automatically non-breaking; it still requires consumer impact review across backend and frontend consumers and must pass through the appropriate shared-contract gate before adoption.

**Current collection contract (IGR-05B / PR #49):** `RiskAssessmentCollectionResponse` is implemented and enforced in both [`backend/app/domain/assessment.py`](../backend/app/domain/assessment.py) and [`frontend/src/api/contracts.ts`](../frontend/src/api/contracts.ts). It carries `items`, `total_count`, effective `window_start` / `window_end`, optional `facility_id`, and `engine_version`. The TypeScript contract exists for future collection consumption; the current UI does not render a ranked collection queue.

| Contract Symbol / Concept | Governance Category | Source Path | Current Guarantee & Invariants | Producer / Owner | Primary Consumers | Potential Extension Direction / Impact Notes | Cross-Cutting Change (Requires Gate) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **`RiskAssessment`** | `IMPLEMENTED / ENFORCED CONTRACT` | [`backend/app/domain/assessment.py`](../backend/app/domain/assessment.py), [`frontend/src/api/contracts.ts`](../frontend/src/api/contracts.ts) | Core domain entity. Strict invariant: `insufficient_data` strictly forbids `risk` and `deterioration_horizon`; `assessed` strictly requires non-null `risk`. Extra fields forbidden (`extra="forbid"`). | Igor (Backend) / Vladimir (Contract) | Frontend UI, API serializers, Demo runner | Adding optional fields with default `None` (must update backend and frontend in sync following shared-contract review). | Modifying invariants, renaming fields, altering nullability rules, adding mandatory fields. |
| **`AssessmentStatus`** | `IMPLEMENTED / ENFORCED CONTRACT` | [`backend/app/domain/assessment.py`](../backend/app/domain/assessment.py), [`frontend/src/api/contracts.ts`](../frontend/src/api/contracts.ts) | Enum with exactly two values: `"assessed"` and `"insufficient_data"`. Governs degraded state handling. | Igor (Backend) / Vladimir (Contract) | Frontend UI (`HomePage.tsx`, `AssessmentCard.tsx`), Analytics engine | None without coordinated contract version bump. | Adding new statuses (e.g. `"degraded"`, `"error"`), changing string values. |
| **`RiskEstimate`** | `IMPLEMENTED / ENFORCED CONTRACT` | [`backend/app/domain/assessment.py`](../backend/app/domain/assessment.py), [`frontend/src/api/contracts.ts`](../frontend/src/api/contracts.ts) | `score: float` bounded in `[0.0, 1.0]`. Optional `band: RiskBand` (`"low"`, `"moderate"`, `"high"`). Not guaranteed to be a calibrated probability. | Analytics layer (future) / Igor | Frontend UI, Evaluation framework | Adding metadata (e.g. quantile intervals) as optional fields following consumer impact review. | Removing score, altering `[0,1]` bounds, changing `RiskBand` enum values. |
| **`DeteriorationHorizon`** | `IMPLEMENTED / ENFORCED CONTRACT` | [`backend/app/domain/assessment.py`](../backend/app/domain/assessment.py), [`frontend/src/api/contracts.ts`](../frontend/src/api/contracts.ts) | Strictly nullable enclosing object. When present, `starts_at: datetime` required; `ends_at: datetime | null` optional. Must remain null when horizon is unsupported. | Analytics layer (future) / Igor | Frontend UI, Operator decision display | Adding optional duration fields (e.g. `hours_remaining`) following consumer impact review. | Making horizon mandatory, inferring fake dates under `insufficient_data`. |
| **`AssessmentFactor`** | `IMPLEMENTED / ENFORCED CONTRACT` | [`backend/app/domain/assessment.py`](../backend/app/domain/assessment.py), [`frontend/src/api/contracts.ts`](../frontend/src/api/contracts.ts) | Structured list of factors. Each has `code: str`, `category: FactorCategory`, `effect: FactorEffect`, `summary: str`, and `evidence_references: list[str]`. Not a causal claim by default. | Explainability layer (future) / Igor | Frontend UI (`AssessmentCard.tsx`), Audit trail | Adding new `FactorCategory` or `FactorEffect` enum members (requires coordinated review). | Turning factors into unstructured strings, removing evidence references. |
| **`Recommendation`** | `IMPLEMENTED / ENFORCED CONTRACT` | [`backend/app/domain/assessment.py`](../backend/app/domain/assessment.py), [`frontend/src/api/contracts.ts`](../frontend/src/api/contracts.ts) | Structured object: `action_code`, `label`, `priority: RecommendationPriority`, `rationale_codes: list[str]`, and `requires_human_review: bool` (default `True`). Absent in current foundation fixture. | Recommend layer (future) / Igor | Frontend UI, Operator workflow | Adding optional fields such as expected turnaround window (requires review). | Free-form LLM text generation, removing `requires_human_review`, claiming causal loss reduction without validation. |
| **`Reliability`** | `IMPLEMENTED / ENFORCED CONTRACT` | [`backend/app/domain/assessment.py`](../backend/app/domain/assessment.py), [`frontend/src/api/contracts.ts`](../frontend/src/api/contracts.ts) | Always present. Contains `level: ReliabilityLevel` (`"unavailable"`, `"low"`, `"medium"`, `"high"`), optional `confidence_score: float` in `[0,1]`, `reason_codes: list[str]`, and `missing_requirements: list[str]`. | Analytics / Orchestration / Igor | Frontend UI (`AssessmentCard.tsx`), Operator trust | Adding new reason codes following consumer impact review. | Populating fake confidence scores without validated interpretation, omitting missing requirements. |
| **`Provenance`** | `IMPLEMENTED / ENFORCED CONTRACT` | [`backend/app/domain/assessment.py`](../backend/app/domain/assessment.py), [`frontend/src/api/contracts.ts`](../frontend/src/api/contracts.ts) | Contains `contract_version` (`"1.0.0"`), `engine_tier` (`"fixture"`, `"deterministic_baseline"`, `"learned_model"`), `engine_version`, `generated_at: datetime`, optional `source_dataset_id`, `simulation: bool`, and `notice: str`. | Orchestration / Igor | Frontend UI, Pitch audit, Evaluation logging | **IMPLEMENTED / ENFORCED IN CODE (RBS-01 / PR #42) — initial HG-R5 dataset-backed runtime release:** `engine_tier=deterministic_baseline`, `engine_version=baseline-crop-median-v1-p1-s2024`, `source_dataset_id=training-agrifood-snapshot-v1`, `simulation=true`, notice `SIMULATION / training challenge dataset / deterministic baseline / not production deployment` (ADR 0005 D2/D3). Dataset ID identifies the pinned assessment-source snapshot, not the fit/release; artifact lineage distinguishes training membership. Public schema and fixture remain unchanged; no future global provenance policy is implied. | Omitting simulation flags for synthetic fixtures, misrepresenting fixture results as real model outputs. |
| **API Endpoints** | `IMPLEMENTED / ENFORCED CONTRACT` | [`backend/app/api/routes.py`](../backend/app/api/routes.py) | Health and synthetic demo routes remain. `GET /api/v1/assessments/{batch_id}` returns a dataset-backed baseline `RiskAssessment` (RBS-01 / PR #42); `GET /api/v1/assessments` returns a ranked `RiskAssessmentCollectionResponse` (IGR-05B / PR #49). | Igor (Backend) | Frontend API client (`client.ts`), Smoke tests, Demo runbook | Collection serving uses configurable paired replay bounds, optional facility filter, global `risk.score DESC, batch_id ASC` ranking before limit/offset slicing, default `limit=20` and max `limit=50`, and fail-closed mapping/scoring. The half-open dispatch window defaults under IGR05-D2R to `2025-11-29T00:00:00Z <= dispatch_datetime < 2025-12-01T00:00:00Z` only when both bounds are omitted. One bound or an invalid interval returns 400; unknown facility 404; invalid pagination 422; collection failure 500; unavailable runtime 503; `Cache-Control: no-store`. The frontend consumes only the single-batch real route so far. | Altering existing route paths, changing HTTP status codes, removing existing endpoints. |
| **HealthResponse / analytics readiness** | `IMPLEMENTED / ENFORCED CONTRACT (RBS-01 / PR #42)` | `backend/app/domain/assessment.py`, `frontend/src/api/contracts.ts`, [ADR 0005 D6](./decisions/0005-runtime-baseline-serving.md) | Synchronized backend/TS: `analytics: "not_configured" | "ready" | "unavailable"`. State reflects runtime readiness: `not_configured` (settings unset), `ready` (snapshot + artifact loaded/validated), `unavailable` (configured resources failed loading/validation). Top-level `status="ok"` and HTTP 200 represent process/application liveness. | Igor / Vladimir; prscr consumer | Frontend (`BackendStatus.tsx`), API tests | Implemented and verified across backend, frontend TypeScript contracts, and API tests. Frontend renders humanized status. | Further health changes beyond ADR 0005 require review. |
| **Frontend Consumption** | `IMPLEMENTED / ENFORCED CONTRACT` | [`frontend/src/api/client.ts`](../frontend/src/api/client.ts), [`frontend/src/pages/HomePage.tsx`](../frontend/src/pages/HomePage.tsx) | React shell handles connection and lookup states, calls `GET /api/v1/assessments/{batch_id}` through `getAssessment()`, and renders the returned single-batch assessment with 404/409/503 feedback (PUX-11A / PR #46). The ranked multi-batch collection queue is not implemented in the UI. | prscr (UX/Demo/QA) | Operator, Demo presenter | Collection client and queue presentation are the next UX slice under accepted contracts. | Hardcoding mock numbers that bypass backend responses, failing to handle unavailable/error states. |
| **Prediction Boundary ($T_{assess} = T_{dispatch}$)** | `FIXED CHALLENGE / SPONSOR CONSTRAINT` | [`sponsor_pack/README.md`](../sponsor_pack/README.md), [`docs/challenge_canon.md`](./challenge_canon.md), [`docs/evaluation.md`](./evaluation.md) | Prediction moment is strictly $T_{assess} = T_{dispatch}$. Features must only use data available at or before dispatch. Arrival checks, actual transit delay/incidents, realized en-route telemetry, and final outcomes are strictly forbidden prediction inputs. Non-negotiable challenge invariant. | Sponsor (Rule) / Viktor (Audit) | Feature engineering, Analytics, Model training, Evaluation | None (Fixed challenge constraint). | Using arrival inspection, realized transit delay, or final outcomes in features or explanations. Cannot be altered by VLD-02 for technical convenience. |
| **Modular Monolith Architecture** | `ACCEPTED DECISION` | [`docs/architecture.md`](./architecture.md), [`docs/decisions/0001-foundation-architecture.md`](./decisions/0001-foundation-architecture.md) | Single repository modular monolith: React+TS frontend, FastAPI+Python backend, typed HTTP boundaries, batch/on-demand MVP, deterministic baseline first, ML optional, LLM outside critical path, stateless foundation. | Vladimir (Integrator) / SoS Team | Entire team | Internal refactoring within existing layer directories. | Introducing microservices, message queues, Docker/Kubernetes requirements, external DB dependencies without a formal decision gate. |
| **Production Ingestion & BatchInput** | `ACCEPTED DECISION (ADR 0002) / IMPLEMENTED IN CODE (IGR-03)` | [`backend/app/domain/batch.py`](../backend/app/domain/batch.py), [`backend/app/ingestion/canonical_mapper.py`](../backend/app/ingestion/canonical_mapper.py), [`docs/decisions/0002-predictive-input-semantics.md`](./decisions/0002-predictive-input-semantics.md) | Canonical `BatchAssessmentInput` semantics, 73-field eligibility matrix, and temporal leakage boundary accepted under ADR 0002; typed domain models and deterministic raw→canonical mapper implemented and tested (IGR-03, PR #28). Enforces $T_{assess} \equiv T_{dispatch}$, restricts telemetry to $T_{entry} \le t \le T_{dispatch}$, preserves missingness as `None`, maps planned logistics, and validates fail-closed joins. IGR-04A/B scoring and construction, RBS-01 runtime serving, and IGR-05B collection serving are implemented. | Vladimir (Decision) / Igor (Implementation) | Ingestion pipeline, Analytics engine | Ingestion produces canonical models for both single-batch and collection assessment. Frontend single-batch lookup is implemented; collection queue presentation remains deferred. | Implementing feature engineering, imputation, or analytics scoring inside the ingestion task. |
| **Analytics Baseline & Deterioration Horizon** | `IMPLEMENTED: IGR-04A / IGR-04B / RBS-01 / IGR-05B` | `backend/app/analytics/crop_median_baseline.py`, `backend/app/services/baseline_assessment.py`, `backend/app/services/collection_assessment.py`, `backend/app/runtime/`, `backend/artifacts/`, [ADR 0003](./decisions/0003-assessment-evaluation-semantics.md), [ADR 0005](./decisions/0005-runtime-baseline-serving.md) | IGR-04A fits explicit training records and scores canonical inputs; IGR-04B builds RiskAssessment from fitted baseline + input + caller provenance. Null band/horizon/recommendation, empty baseline factors and unavailable reliability persist. Public demo remains synthetic. | Igor / Viktor / Vladimir | Assessment service, HTTP consumers | Single-batch GET (RBS-01 / PR #42) and bounded, globally ranked collection GET (IGR-05B / PR #49) are implemented. The frontend consumes single-batch assessments; its collection queue remains deferred. | No new minimum/fallback semantics; valid canonical input the baseline cannot legitimately assess triggers STOP — HUMAN DECISION REQUIRED. |

---

# 3. Workstream producer → consumer map

This map establishes the flow of dependencies across the five human workstream owners. Rather than a rigid waterfall, four parallel evidence streams feed into the Integrator decision gates, while downstream implementation proceeds along task-specific dependency paths.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    PARALLEL RECONNAISSANCE EVIDENCE                     │
│                                                                         │
│  Alisa product/domain evidence ────────┐                                │
│  Viktor data/evaluation evidence ──────┤                                │
│  Igor technical recon/evidence ────────┼──► Vladimir integration /      │
│  prscr UX/demo evidence ───────────────┘    decision gate (VLD-02)      │
└────────────────────────────────────────────────────┬────────────────────┘
                                                     │
                                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              TASK-SPECIFIC DOWNSTREAM IMPLEMENTATION PATHS              │
│                                                                         │
│  • Ingestion & Input Pipelines:                                         │
│    VDR-01 Accepted ──► IGR-02 Raw Ingestion & Diagnostics IMPLEMENTED   │
│    VDR-01 + VDR-02 Accepted ──► VLD-02A Accepted (ADR 0002) ──►        │
│    IGR-03 Canonical Input Model & Mapper IMPLEMENTED (PR #28)           │
│                                                                         │
│  • Deterministic Baseline & Risk Engine:                                │
│    Target & Evaluation Semantics (Viktor) + Method Evidence             │
│    [+ Domain Rules (Alisa) if method relies on agronomic thresholds]    │
│    ──► ADR 0003 ──► IGR-04A implemented ──► IGR-04B implemented       │
│    ──► VLD-R5 recon (evidence) ──► HG-R5 / ADR 0005 (decision)         │
│    ──► RBS-01 single-batch ──► IGR-05B collection backend             │
│    ──► PUX-11A single-batch UI ──► later queue UI ──► VLD-03          │
│                                                                         │
│  • User Experience & Operator Dashboard:                                │
│    PUX Recon/Flow ──► Stable API Contracts ──► prscr Operator UI        │
│                                                                         │
│  • Predictive Modeling (Optional ML Tier):                              │
│    Accepted Baseline + Justification (Viktor) ──► VLD-02 ──► Igor Model │
└────────────────────────────────────────────────────┬────────────────────┘
                                                     │
                                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     VLADIMIR FINAL INTEGRATION GATES                    │
│  • VLD-03: End-to-End Functional Verification & Integration Test Suite  │
│  • VLD-04: Runtime Readiness & Operational Demo Runbook                 │
│  • VLD-05: Pitch Consistency & Traceable Evidence Audit                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### Downstream dependencies are task-specific, not monolithic

Downstream implementation does not wait for an all-or-nothing milestone across all workstreams. Decision gates and downstream tasks are bounded strictly to their required evidence:

- **Viktor sequence:** `VDR-02` (temporal chronology and leakage audit) starts only after `VDR-01` (dataset inventory and referential integrity) has been completed and reviewed.
- **Predictive input semantics vs raw parsing:** Accepted `VDR-01` may be sufficient to support a narrowly scoped implementation task for factual raw parsing and structural validation where the task only reflects measured schema and integrity evidence. However, `VDR-02` (temporal leakage audit) is mandatory before predictive/canonical assessment input semantics (`BatchAssessmentInput`) are finalized, including feature eligibility at $T_{dispatch}$, leakage-sensitive transformations, and any mapping that determines what enters predictive analytics. Production `BatchAssessmentInput` and equivalent predictive canonical semantics require the relevant VLD-02 decision before implementation. Technical CSV-reading helpers do not automatically require VDR-02 if they do not establish shared predictive semantics.
- **Later analytical and model work:** A deterministic baseline requires accepted analytical target and evaluation semantics from Viktor, plus whatever evidence its actual method relies upon. Alisa/domain evidence (`APR-01`) is additionally required when the chosen baseline method depends on agronomic thresholds, crop-specific rules, domain interpretation, or action/recommendation semantics. Domain evidence is conditional on the baseline design, not universally mandatory for every possible baseline.
- **Product and domain evidence:** Sourced domain research and operator workflow evidence from Alisa (`APR-01`) is required only for decisions that depend on product or domain meaning (such as action codes, recommendation priorities, operator workflow scope, and domain rule admission). Technical pipeline and data-loading tasks that do not alter domain semantics proceed once their technical evidence is accepted.
- **UX and UI development:** prscr's user interface work proceeds through UX reconnaissance, screen flows, and fixture-backed wireframes under its own sequential workflow (`PUX-00–07`), binding to production backend endpoints once Igor's routes are approved and operational.

## 3.1. Detailed ownership inventory

### Vladimir — Integrator
- **Currently owns:** System architecture continuity, cross-workstream contracts, boundary definitions, integration gates (VLD-01 to VLD-05), conflict resolution, and final solution assembly.
- **Accepted output that currently exists:** The VLD-01 baseline of [`docs/integration_contract.md`](./integration_contract.md), [`docs/team_roles.md`](./team_roles.md), [`docs/architecture.md`](./architecture.md), [`docs/decisions/0001-foundation-architecture.md`](./decisions/0001-foundation-architecture.md), [`docs/decisions/0002-predictive-input-semantics.md`](./decisions/0002-predictive-input-semantics.md) (VLD-02A / ADR 0002, PR #16), [`docs/data_contract.md`](./data_contract.md), [`docs/domain_rules.md`](./domain_rules.md), [`docs/evaluation.md`](./evaluation.md), [`docs/challenge_canon.md`](./challenge_canon.md), [`docs/assumptions_unknowns.md`](./assumptions_unknowns.md), [`docs/demo_runbook.md`](./demo_runbook.md), [`docs/workstreams/vladimir-integration.md`](./workstreams/vladimir-integration.md). The historical VLD-R3 update made no new decision. [ADR 0003](./decisions/0003-assessment-evaluation-semantics.md) records Vladimir's approved D1–D10, including D3/D4 overrides, integrated through PR #21. [ADR 0004](./decisions/0004-mvp-product-scope.md) records Vladimir's approved MVP product scope decisions APR2-D1–D6 (2026-09-21). [ADR 0005](./decisions/0005-runtime-baseline-serving.md) records his explicit HG-R5 D1–D7 acceptance (2026-09-22): initial lifecycle, provenance, single-batch GET, failure transport and health policy; implemented in code and Human Integrated via RBS-01 (PR #42).
- **Future planned output:** Later gates for unresolved engine, calibration, explanation and action policies; VLD-03 integration verification, VLD-04 operational runbook, and VLD-05 claim audit. ADR 0003 accepted task/target, baseline/evaluation and output policies; ADR 0005 defined initial serving policy, fulfilled by RBS-01. Backend collection serving is fulfilled by IGR-05B; frontend queue presentation, future learned engine, engine minimums beyond the current baseline, future production training/retraining and deployment remain unresolved/deferred.
- **Who consumes output:** All workstream owners (Igor, Viktor, prscr, Alisa).
- **Downstream work blocked until evidence exists:** Decision gates are task-specific. Canonical predictive-input semantics (ADR 0002) and canonical mapping (IGR-03) are complete. ADR 0003 accepts bounded target/evaluation/baseline and output semantics. ADR 0004 accepts MVP product scope decisions APR2-D1–D6. PUX-08 is integrated as DRAFT FOR REVIEW (governed by ADR 0004 where applicable); APR-02 source documents remain mixed research/spec artifacts. IGR-04A/04B and RBS-01 baseline serving (PR #42), PUX-11A single-batch frontend lookup (PR #46), and IGR-05B backend collection serving (PR #49) are implemented. Frontend collection queue/presentation and deployment follow separately; no production learned engine is selected or required. New backend model or frontend claims still require their specific evidence and decisions.

### Viktor — Data & Evaluation Owner
- **Currently owns:** Dataset profiling, schema verification, data quality analysis, join validation, temporal analysis, leakage prevention, identifying usable labels, producing target/evaluation evidence and proposals, evaluation methodology, baseline comparison, and guarding against false precision and misleading metrics.
- **Accepted output that currently exists:** [`docs/data_recon/01_dataset_inventory.md`](./data_recon/01_dataset_inventory.md) (VDR-01, PR #7); [`docs/data_recon/02_temporal_leakage.md`](./data_recon/02_temporal_leakage.md) (VDR-02, PR #14); [`docs/data_recon/03_target_horizon_feasibility.md`](./data_recon/03_target_horizon_feasibility.md) (VDR-03, PR #18, ACCEPTED / INTEGRATED); [VDR-04A report](./data_recon/04_dispatch_predictability.md) and [results](./data_recon/04_dispatch_predictability_results.json) (PR #20, ACCEPTED / INTEGRATED); workstream contract [`docs/workstreams/viktor-data-recon.md`](./workstreams/viktor-data-recon.md). The supplied dataset remains the source snapshot.
- **Pending work / future output:** VDR-04A already provides protocol comparisons, baseline results and predictability/ranking feasibility. Future bounded work includes an evaluation harness under ADR 0003, model/feature comparisons and any separate production learned-engine acceptance; no model is selected here.
- **Who consumes output:** Vladimir (integration gates), Igor (ingestion, canonical entity modeling, analytics), prscr (realistic data distributions and batch scenarios), Alisa (grounding product workflows in real data limits).
- **Downstream work blocked until evidence exists:** Accepted VDR-01, VDR-02, and VDR-03 satisfy the inventory, temporal/leakage, and target/horizon feasibility evidence prerequisites. Canonical predictive-input semantics were accepted under ADR 0002. VDR-03 established that candidate outcomes have known relationships and that exact continuous deterioration countdown is unsupported, but explicitly did not select a target, metric, split, baseline, model, or runtime horizon policy. VDR-04A now supplies that evidence; ADR 0003 accepts target, baseline, evaluation and null-horizon semantics. Later harness/model work remains separately contracted; feasibility does not select a production model.

### Igor — Technical Deputy
- **Currently owns:** Backend and application-layer implementation, API routes, implementation of backend/application models within accepted shared contracts, ingestion logic, deterministic baseline engine, optional learned model integration, explainability and recommendation services. Igor may decide implementation details inside agreed technical scope, but does not independently own changes to global/shared domain contracts.
- **Current IGR-05B output:** `backend/app/services/collection_assessment.py`, `GET /api/v1/assessments`, shared `RiskAssessmentCollectionResponse` in Python and TypeScript, and collection tests are implemented, accepted and Human Integrated through PR #49. The D2R default amendment changes only omitted query bounds.
- **Accepted output that currently exists:** [`docs/recon/IGR-01-technical-recon.md`](./recon/IGR-01-technical-recon.md) (IGR-01, PR #8); FastAPI application skeleton (`backend/app/main.py`, `backend/app/api/routes.py`), Pydantic output models (`backend/app/domain/assessment.py`), synthetic demo fixture (`backend/app/services/demo_assessment.py`), backend tests (`backend/tests/`), workstream contract [`docs/workstreams/igor-technical-recon.md`](./workstreams/igor-technical-recon.md); IGR-02 raw CSV reading, manifest, and structural diagnostics (`backend/app/ingestion/raw_reader.py`, `structural_manifest.py`, `diagnostics.py`, PR #21); IGR-03 typed canonical `BatchAssessmentInput` domain models and deterministic raw-to-canonical mapper (`backend/app/domain/batch.py`, `backend/app/ingestion/canonical_mapper.py`, `backend/tests/test_ingestion_canonical.py`, PR #28); IGR-04A deterministic crop-median engine (`backend/app/analytics/crop_median_baseline.py`) and IGR-04B internal assessment service (`backend/app/services/baseline_assessment.py`); RBS-01 offline artifact generation (`scripts/generate_baseline_artifact.py`), versioned baseline artifact (`backend/artifacts/baseline-crop-median-v1-p1-s2024.json`), runtime validation and context provider (`backend/app/runtime/`), single-batch assessment route `GET /api/v1/assessments/{batch_id}` (`backend/app/api/routes.py`), health synchronization, and contract tests (`backend/tests/test_runtime_baseline.py`, PR #42).
- **Future planned output:** Backend single-batch and collection serving are complete. Frontend collection queue, learned/explanation/recommendation/deterioration work and deployment remain separately gated or deferred.
- **Who consumes output:** prscr (API responses for UI consumption), Vladimir (system coherence and test verification).
- **Downstream work blocked until evidence exists:** RBS-01 single-batch serving, PUX-11A frontend real-route lookup, and IGR-05B backend collection serving are complete and integrated. Frontend ranked queue, learned models, recommendations, deterioration prediction, and new engine minimum policies remain subject to their respective decisions/evidence.

### prscr — UX, Demo + QA
- **Currently owns:** Frontend implementation and operator-facing workflow, user interface, presentation of risks, factors, and actions, loading/degraded/insufficient-data states, demo reliability, and exploratory QA.
- **Current PUX-11A output:** PR #46 implemented real single-batch assessment lookup through `getAssessment(batchId)` and `GET /api/v1/assessments/{batch_id}`. Ranked collection consumption and queue presentation remain the next UX slice.
- **Accepted output that currently exists:** [`prscr_ux_demo_qa_report.md`](../prscr_ux_demo_qa_report.md) (PUX-00–07, PR #9, repository root); React+TS+Vite shell (`frontend/src/`), connection state management (`HomePage.tsx`), synthetic assessment rendering (`AssessmentCard.tsx`), health status display (`BackendStatus.tsx`), typed API client (`api/client.ts`, `api/contracts.ts`), workstream contract [`docs/workstreams/prscr-ux-demo-qa.md`](./workstreams/prscr-ux-demo-qa.md); PUX-08 data-to-UX reconciliation report ([`docs/recon/PUX-08-data-ux-reconciliation.md`](./recon/PUX-08-data-ux-reconciliation.md), PR #22), integrated as **`DRAFT FOR REVIEW / NOT CANON`**. Acceptance of recon artifacts does not make their provisional wireframes, API proposals, or candidate workflows accepted decisions, or their planned QA cases executed tests.
- **Future planned output:** Agreed UX specifications, interactive batch dashboard, detailed factor inspection UI, demo flow execution, and automated/exploratory QA execution evidence.
- **Who consumes output:** Vladimir (demo verification and UI claim audit), Igor (API usability requirements), judges/operators (user interface experience).
- **Downstream work blocked until evidence exists:** Single-batch real lookup is implemented, and the backend collection endpoint is available. Frontend ranked queue/presentation, final batch selection tables, risk meters, and recommendation widgets remain separate UX work under accepted product scope (ADR 0004) and their own evidence or decision prerequisites. PUX-08 remains draft evidence.

### Alisa — Product Owner
- **Currently owns:** Challenge interpretation, user and operator problem framing, requirement and mentor clarification tracking, domain research (post-harvest practices, cold chain management), recommendation semantics, and pitch/presentation narrative.
- **Accepted output that currently exists:** Workstream contract [`docs/workstreams/alisa-product-recon.md`](./workstreams/alisa-product-recon.md); research evidence package [`docs/product_recon/`](./product_recon/) (APR-01 steps 0–5, PR #17).
- **Current APR-01 status:** APR-01 steps 0–5 are **DELIVERED / INTEGRATED through [PR #17](https://github.com/Slave-of-Skynet/training_agrifood/pull/17)** and **ACCEPTED AS PRODUCT/DOMAIN RESEARCH EVIDENCE**. Individual research notes retain their own `FACT`, `DOMAIN FACT`, `INFERENCE`, `UNKNOWN`, and `NOT CANON` labels; APR-01 research is **NOT AUTOMATICALLY CANON AS A WHOLE** and does not override official challenge materials or accepted data evidence.
- **Future planned output:** Candidate rule reviews for `docs/domain_rules.md`, pitch deck narrative structure, and follow-up domain clarifications.
- **Who consumes output:** Vladimir (ensuring solution solves the right problem), prscr (operator mental model and information hierarchy), Igor (business logic constraints), Viktor (interpreting target meaning and business error costs).
- **Downstream work blocked until evidence exists:** Final recommendation labels and operator action scopes are blocked until external agricultural and post-harvest sources are reviewed and accepted as decisions. Product/domain evidence is required only for decisions that depend on product/domain meaning (including agronomic thresholds if required by the chosen baseline). Pitch claims regarding economic loss reduction remain blocked on validated action-effect evidence; ranking evaluation alone cannot justify them.

---

# 4. Integration boundary matrix

Every transition across system layers represents an integration boundary. This matrix defines the contracts, current statuses, governing UNKNOWN areas, evidence requirements, and decision authorities for every boundary.

| Boundary | Producer | Consumer | Current Contract | Current Status | Relevant Canonical UNKNOWN Area(s) | Evidence Owner & Task | Evidence Required Before Decision | Decision / Gate Owner | What Downstream Work is Unsafe if Unresolved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **B1: Raw Dataset → Ingestion** | Sponsor pack (`sponsor_pack/data/*.csv`) | Ingestion layer (`backend/app/ingestion/`) | Supplied schema plus accepted [VDR-01 snapshot inventory/integrity evidence](./data_recon/01_dataset_inventory.md); IGR-02 structural manifest and diagnostics (`backend/app/ingestion/structural_manifest.py`, `diagnostics.py`). | **FACT: SUPPLIED SNAPSHOT EMPIRICALLY PROFILED; IGR-02 RAW INGESTION & DIAGNOSTICS IMPLEMENTED (PR #21).** Observed schema/types, counts, integrity and relationships verified. | Field names and types, Joins and entity relationships, Dataset size | Viktor (`VDR-01`, accepted); Igor (`IGR-02`, implemented) | VDR-01 satisfied raw parsing evidence; IGR-02 implements raw parsing and diagnostics. Production validation of unseen external schemas and external repair/exclusion policies remain open. | Vladimir (bounded contract / VLD-02 if shared contract changes) | Raw ingestion must not silently repair/drop data, assume future datasets have identical cardinalities, or establish predictive/analytics semantics. |
| **B2: Ingestion → Canonical Representation** | Ingestion layer (`backend/app/ingestion/`) | Canonical entity models (`backend/app/domain/batch.py`) | **BatchAssessmentInput: ACCEPTED under [ADR 0002](./decisions/0002-predictive-input-semantics.md); IMPLEMENTED in IGR-03 (PR #28).** | **IMPLEMENTED & VERIFIED IN CODE (IGR-03, PR #28).** Deterministic raw→canonical mapper enforces $T_{assess} \equiv T_{dispatch}$, restricts telemetry to storage stay, preserves missingness as `None`, maps planned logistics, and validates fail-closed joins. IGR-04A scoring, IGR-04B internal assessment, and RBS-01 runtime serving are implemented outside ingestion. | Field names and types, Joins and entity relationships, Assessment-time availability, Missing and noisy data | Viktor (`VDR-01` accepted; `VDR-02` accepted), Vladimir (ADR 0002 accepted), Igor (`IGR-03` implemented) | VDR-01 supplied grain and join paths; VDR-02 supplied dispatch availability and leakage evidence; ADR 0002 accepted canonical input semantics; IGR-03 implemented mapping. | Vladimir (ADR 0002 accepted; Igor implemented in IGR-03) | Implementing feature engineering, imputation, or analytics scoring inside the ingestion task. Downstream analytics engines must consume canonical inputs rather than raw CSVs. |
| **B3: Canonical Representation → Analytics Engine** | Canonical entity models (`backend/app/domain/batch.py`) | Analytics engine (`backend/app/analytics/`) | ADR 0002 input semantics; IGR-03 `BatchAssessmentInput`; existing `RiskAssessment` shape; ADR 0003 D1–D10 integrated, with D3/D4 overrides. | **IMPLEMENTED & ENFORCED IN CODE (IGR-03, IGR-04A/B, RBS-01 / PR #42).** Canonical input mapped, crop-median baseline fitted offline into versioned artifact, loaded into runtime context, and evaluated by assessment service. No learned engine or new engine-minimum policy is selected. | Measurement frequency and time series, Assessment-time availability, Outcomes and candidate labels, Deterioration timing, Agronomic rules and thresholds | Viktor (VDR-01–04A accepted), Vladimir (ADR 0002/0003), Igor (IGR-03 implemented, later analytics implementation); Alisa for future domain-dependent claims | Target, score, baseline and P1/P2/P3 policy accepted. Canonical inputs available. ADR 0005 resolves initial artifact, fit identity and serving policy; fulfilled by RBS-01. Subsequent fallback, transformations and learned engines remain separately gated. | Vladimir (ADR 0003 accepted; later bounded contracts) | Analytics inside IGR-03, invented missingness/threshold policies, mixed tiers/versions without comparability validation, or treating VLD-02B as implementation authorization. |
| **B4: Analytics → RiskAssessment** | Analytics engine / Services | Public domain model (`backend/app/domain/assessment.py`) | Stable `RiskAssessment` contract: `status`, `risk`, `deterioration_horizon`, `factors`, `recommendation`, `reliability`, `provenance`. | **IMPLEMENTED & SERVED (RBS-01 / PR #42):** IGR-04B builds scored baseline RiskAssessment with caller provenance; served via `GET /api/v1/assessments/{batch_id}`. Public demo fixture remains distinct and returns synthetic `insufficient_data`. | Outcomes and candidate labels, Deterioration timing, Intervention and action effects, Missing and noisy data | Viktor (target/baseline), Alisa (action meaning), Igor (orchestration) | ADR 0003 accepts severity/ranking semantics, null horizon/recommendation and unavailable reliability. Later verification must enforce these and validate model-contribution explanation methods. | Vladimir (VLD-02 Decision Gate / VLD-03 Verification Gate) | Returning fake risk scores, ungrounded deterioration dates, or unverified recommendations to the public contract. |
| **B5: RiskAssessment → API** | FastAPI routes (`backend/app/api/routes.py`) | HTTP response / JSON serialization | Health, synthetic demo, single-batch assessment and collection assessment routes serialize through Pydantic contracts. | **OPERATIONAL (FOUNDATION + RBS-01 + IGR-05B):** `GET /api/v1/health`, `GET /api/v1/demo/assessment`, real `GET /api/v1/assessments/{batch_id}` (PR #42), and ranked `GET /api/v1/assessments` (PR #49). | Realtime source, Persistence needs | Igor (`IGR-01`, IGR-05B API implementation) | Technical verification of serialization, error handling, performance, and endpoint parameterization. | Vladimir (VLD-02 Gate) with Igor | Altering existing public routes; adding unversioned breaking parameters; exposing internal errors. |
| **B6: API → Frontend** | API endpoints | React UI client (`frontend/src/api/client.ts`, `contracts.ts`) | TypeScript interfaces mirror Pydantic assessment and collection models; fetch client handles single-batch loading/success/error. | **SINGLE-BATCH REAL INTEGRATION IMPLEMENTED (PUX-11A / PR #46); RANKED COLLECTION UI DEFERRED.** The shared collection type is synchronized but the UI does not request or render the collection endpoint. | Realtime source | prscr (`PUX-11A`, UI implementation) & Alisa (`APR-01`) | Collection client and operator queue presentation remain the next UX implementation slice. | Vladimir (VLD-02 / VLD-03 Gate) with prscr & Igor | Manual divergence between TypeScript interfaces and Python Pydantic models; UI crashing on missing optional fields; building workflows disconnected from operator realities. |
| **B7: Assessment Semantics → Demo** | Application UI & Backend | Demo script & Operator experience | [`docs/demo_runbook.md`](./demo_runbook.md): Verified local startup, health check, synthetic fixture rendering, failure states. | **FOUNDATION ONLY** (Proves connectivity, not agricultural validity). | Hosting constraints, Persistence needs | prscr (Demo flow), Vladimir (Runbook readiness) | Reproducible step-by-step runbook; proven fallback for offline/backend failure; clearly labeled synthetic data. | Vladimir (VLD-04 Gate) | Presenting synthetic demo data as real prediction results; live demo failure due to unhandled exceptions or network dependencies. |
| **B8: Verified Behaviour → Product Claims / Pitch** | Implemented system & Evaluation reports | Pitch deck, README, team claims | Canon rule: Every claim must be classified (FACT, DECISION, UNKNOWN, etc.) and backed by reproducible evidence. | **CLAIMS GATED:** accepted benchmark observations may be cited with limits; no production accuracy or causal loss-reduction promise is established. | Monetary and quantity fields, Crop diversity, Learned model family, Outcomes and candidate labels | Vladimir (VLD-05 Gate), Viktor (evaluation), Alisa (narrative) | Fully executed test suites, reproducible evaluation notebooks/reports, cited domain literature, verified audit trail. | Vladimir (VLD-05 Gate) | Discrediting team credibility before judges with exaggerated claims, unsubstantiated loss-reduction figures, or fabricated accuracy metrics. |

---

# 5. UNKNOWN → evidence → decision triggers

[`docs/assumptions_unknowns.md`](./assumptions_unknowns.md) is and remains the **sole canonical global UNKNOWN register** for the project.

The table below does **not** reproduce or duplicate the descriptions or general questions from that register. Instead, it defines strictly the **operational integration relationships** around those UNKNOWN areas: which integration boundary is affected, who owns the evidence task, what specific evidence triggers a VLD-02 decision gate, and which downstream workstream consumers are blocked until that gate is closed. The required-evidence column includes both already accepted observations and outstanding decision inputs; the current-status column separates them. No compound UNKNOWN is closed solely because inventory evidence exists.

| Canonical UNKNOWN Area (from [`assumptions_unknowns.md`](./assumptions_unknowns.md)) | Affected Boundary | Evidence Owner & Task | Specific Evidence Required | Decision Trigger & Gate | Downstream Consumers Blocked | Current Status |
| --- | --- | --- | --- | --- | --- | --- |
| **Field names and types** | B1 (Ingestion), B2 (Canonical) | Viktor (`VDR-01`), Vladimir (`VLD-02A`), Igor (`IGR-02`, `IGR-03`) | Measured row counts, parsing exceptions, column null percentages, type conformance across all 8 tables; normative mapping table. | VLD-02A Gate ([ADR 0002](./decisions/0002-predictive-input-semantics.md)): Adopted canonical input contract and 73-field eligibility matrix. | Igor: Factual raw parsing and canonical mapping implemented (IGR-02, IGR-03). | **VLD-02A ACCEPTED & IGR-03 IMPLEMENTED (PR #28):** Canonical input models and raw→canonical mapper implemented for supplied schema under ADR 0002. Unseen-value behavior beyond implemented validation, future schema drift, and engine-specific requirements remain UNKNOWN. |
| **Joins and entity relationships** | B1 (Ingestion), B2 (Canonical) | Viktor (`VDR-01`), Vladimir (`VLD-02A`), Igor (`IGR-03`) | Tested join integrity among facilities, zones, sessions, batches, checks, shipments, telemetry, outcomes. Orphan counts. | VLD-02A Gate ([ADR 0002](./decisions/0002-predictive-input-semantics.md)): Adopted canonical entity boundaries and join rules. | Igor: Relational join and fail-closed cardinality checks implemented (IGR-03). | **VLD-02A ACCEPTED & IGR-03 IMPLEMENTED (PR #28):** Entity boundaries, authoritative joins, and fail-closed cardinality enforcement implemented in code/tests for supplied snapshot. Future-data deviations and unexpected cardinalities in live operational streams remain UNKNOWN. |
| **Dataset size** | B1 (Ingestion), Storage architecture | Viktor (`VDR-01`), Igor (`IGR-01`) | Exact file sizes, memory footprint when loading tables (especially `sensor_readings.csv`), query latency. | VLD-02 Gate: Decide whether in-memory processing suffices or indexed storage is required. | Igor: Data loading architecture; Vladimir: Operational demo hardware requirements. | **VDR-01 / IGR-01 ACCEPTED:** snapshot counts/sizes known; runtime memory, latency, concurrency and storage choice remain UNKNOWN. |
| **Measurement frequency and time series** | B2 (Canonical), B3 (Analytics) | Viktor (`VDR-01`, `VDR-02`) | Actual sampling intervals (nominal 30 min), timestamp continuity, gap frequencies, out-of-session readings. | VLD-02 Gate: Adopt sensor aggregation windows and missing-telemetry imputation/rejection rules. | Igor: Time-series feature extraction pipelines; Viktor: Baseline feature definitions. | **VDR-01 / VDR-02 ACCEPTED:** sampling/gaps/coverage and dispatch staleness measured (non-truncated batches <= 29.4 min; 204 batches truncated on 2025-12-31). Feature aggregation windows, staleness tolerance, and imputation/rejection policy await later evidence and VLD-02 decision. |
| **Assessment-time availability** | B2 (Canonical), B3 (Analytics) | Viktor (VDR-02/04A accepted), Vladimir (ADR 0002/0003), Igor (IGR-03 implemented) | Audit of all fields at dispatch; list of strictly forbidden future fields (arrival checks, transit delays, final outcomes); shared-zone/chamber leakage audit. | VLD-02A Gate ([ADR 0002](./decisions/0002-predictive-input-semantics.md)): Adopted canonical input semantics, feature eligibility filter, and telemetry boundary ($T_{entry} \le t \le T_{dispatch}$). | Igor: canonical mapping implemented (IGR-03); Viktor: harness under accepted P1/P2/P3. | **DECISION & IMPLEMENTED (IGR-03):** ADR 0002 eligibility unchanged; ADR 0003 accepts evaluation and optional-logistics capability semantics; IGR-03 implements temporal cutoff and leakage exclusions. Transformations, booking stability, and exact fallback remain open. |
| **Outcomes and candidate labels** | B3 (Analytics), B4 (RiskAssessment) | Viktor (VDR-03/04A), Alisa (APR-01 research), Vladimir (ADR 0003) | Distribution of outcome fields (`quality_status`, `loss_fraction_pct`, `quality_score`, `economic_loss_eur`); definition of business risk target. | ADR 0003 D1–D5 accepted task, target, score, ranking, baseline and metrics; remaining policies use later gates. | Viktor: Model training & evaluation; Igor: Analytics engine risk calculation; prscr: UI risk gauge. | **DECISION — ADR 0003 D1–D5:** ranking, loss label, severity score, baseline and evaluation accepted. Label/business provenance and production learned-engine choice remain UNKNOWN. |
| **Deterioration timing** | B3 (Analytics), B4 (RiskAssessment) | Viktor (VDR-03), Alisa (APR-01 research), Vladimir (ADR 0003) | Analysis of whether intermediate `quality_checks` or telemetry provide supportable onset timestamps or shelf-life proxies. | ADR 0003 D6 adopted null horizon; future estimates need event evidence and a decision. | Igor: Horizon estimation logic; prscr: Timeline visualization on frontend. | **DECISION — ADR 0003 D6:** current horizon null; exact countdown unsupported. Event definitions, biological onset and future interval feasibility remain UNKNOWN. |
| **Intervention and action effects** | B3 (Analytics), B4 (RiskAssessment) | Alisa (APR-01 research), Viktor (later effect evidence), Vladimir (ADR 0003) | Sourced domain literature on post-harvest interventions; check if dataset contains action-outcome pairs. | ADR 0003 D9 adopted null recommendation; future action catalogue remains gated. | Igor: Recommendation service; prscr: Action recommendation cards. | **DECISION — ADR 0003 D9:** recommendation null now; future informational actions require a separate gate. Action authority/effects/costs and financial savings remain unestablished. |
| **Monetary and quantity fields** | B3 (Analytics), B8 (Pitch) | Viktor (`VDR-01`, `VDR-03`), Alisa (`APR-01`) | Verification of `economic_loss_eur` derivation and validity for business impact claims. | VLD-02 Gate: Decide if financial impact estimation is supportable in MVP. | Alisa: Pitch ROI claims; Igor: Potential financial loss display. | **VDR-01 / VDR-03 ACCEPTED:** historical formula deterministically reproduced within reported tolerance. Business interpretation, prevented loss, ROI and causal savings remain UNKNOWN; APR-01 accepted as research evidence, not canon. |
| **Crop diversity** | B2 (Canonical), B3 (Analytics) | Viktor (`VDR-01`), Alisa (`APR-01`) | Distribution of crop types in batches; domain storage requirements per crop. | VLD-02 Gate: Decide single-crop MVP focus or multi-crop segmentation. | Igor: Model/rule scoping; Viktor: Subgroup evaluation protocol. | **VDR-01 ACCEPTED; APR-01 ACCEPTED AS RESEARCH EVIDENCE:** crop/cultivar coverage and biological profiles measured. Transferability, rule scope and subgroup sufficiency remain UNKNOWN; APR-01 not automatically canon. |
| **Missing and noisy data** | B2 (Canonical), B4 (RiskAssessment) | Viktor (VDR-01–04A), Igor (later engine contract), Vladimir (ADR 0003) | Frequency of missing sensor readings or missing checks; criteria for triggering `insufficient_data`. | ADR 0003 D7 adopted sufficiency meaning and unavailable reliability; exact minimums remain for later engine contracts. | Igor: Invariant enforcement in application services; prscr: Degraded UI rendering. | **DECISION — ADR 0003 D7:** engine/version-specific sufficiency; unavailable reliability, null confidence. Legitimate optional missingness/truncation is not automatic rejection. Exact minimums, repair and calibration remain UNKNOWN. |
| **Realtime source** | B1 (Ingestion), B5 (API) | Alisa (`APR-01`), Igor (`IGR-01`) | Confirmation of operator workflow needs (batch upload vs scheduled batch vs simulated stream). | VLD-02 Gate: Confirm MVP runtime processing mode (retains batch/on-demand by default). | Igor: API route design; prscr: Upload/run workflow in UI. | **IGR-01 ACCEPTED; APR-01 ACCEPTED AS RESEARCH EVIDENCE:** batch/on-demand decision retained; additional source/workflow requirements unresolved. |
| **Hosting constraints** | B7 (Demo) / Runtime Environment | Vladimir (`VLD-04`), Igor (`IGR-01`), prscr (Demo needs) | Target demonstration environment needs, network connectivity requirements, hardware resources, deployment complexity. | VLD-04 Gate: Environment and platform selection remains under VLD-04 unless an earlier blocker requires a human decision. No hosting provider preselected; remote hosting not required by default. | Vladimir: Demo deployment runbook, final runtime environment setup. | **IGR-01 / PUX-00–07 ACCEPTED AS RECON:** target demo environment remains unresolved; VLD-04 still required. |
| **Agronomic rules and thresholds** | B3 (Analytics), `docs/domain_rules.md` | Alisa (`APR-01`), Viktor (`VDR-01`) | Primary literature sources (FAO, university extension) for temperature/humidity thresholds; data compatibility. | VLD-02 Gate: Formal admission of candidate rules into `docs/domain_rules.md`. | Igor: Deterministic baseline rule implementation (if baseline design relies on agronomic thresholds); prscr: Explanatory factor text. | **VDR-01 ACCEPTED; APR-01 ACCEPTED AS RESEARCH EVIDENCE:** data compatibility and literature sources compiled; formal admission into docs/domain_rules.md remains pending. |
| **Learned model family** | B3 (Analytics) | Viktor (VDR-04A; later comparisons), Vladimir (separate learned-engine acceptance) | Measured performance of deterministic baseline; empirical proof that ML provides meaningful improvement. | VLD-02 Gate: Authorize learned tier implementation in `backend/app/analytics/`. | Igor: Model serialization and inference pipeline integration. | **OBSERVED RESULT:** ranking feasibility and baseline comparisons accepted. **DECISION — ADR 0003 D4/D5/D10:** median baseline accepted; no production learned engine selected or required. Family/hyperparameters/features remain UNKNOWN; direct logistics-enabled telemetry ablation required before removal. |
| **Persistence needs** | Architecture, Storage layer | Igor (`IGR-01`), Viktor (`VDR-01`), Alisa (`APR-01`) | Volume, lifecycle, concurrency, audit, and operator workflow needs; whether in-memory processing suffices or disk/DB persistence is needed. | VLD-02 Gate: May become a VLD-02 cross-cutting decision if accepted evidence shows persistence is required for application implementation. | Igor: Database setup/storage layer (if needed); Vladimir: Architecture consistency. | **VDR-01 / IGR-01 ACCEPTED:** file volume and technical state known; ADR 0005 selects the initial JSON artifact and loaded context; broader workflow, storage/database, scaling and hosting remain unresolved. |

---

### Additional VDR-01 cross-cutting triggers

These reference the corresponding entries in the sole global UNKNOWN register; target ambiguity is already covered by the Outcomes and candidate labels row above.

| Canonical UNKNOWN area | Affected boundary | Evidence available | Evidence / decision still required | Owner / blocked consumers |
| --- | --- | --- | --- | --- |
| Telemetry truncation | B2, B3, B4 | VDR-01/02 identify 204 truncated batches; VDR-04A evaluates them and records crop/season confounding | ADR 0003 D7 prohibits rejection solely for truncation and arbitrary freshness cutoffs. Exact engine windows/imputation/exclusion remain open; reliability unavailable, confidence null. | Viktor + Igor → Vladimir; feature, evaluation and UI consumers |
| Shared chamber / zone-time dependence | B2, B3 | Accepted VDR-01 establishes concurrent chamber sharing; accepted VDR-02 measures 96.33% chamber sharing, 157 chamber-time clusters, and an average of 95.79% of test batches sharing an identical chamber microclimate cluster with training batches in standard randomized 80/20 splits | ADR 0003 D5 accepts P1 primary, P2 mandatory robustness, P3 non-defensible diagnostic. Residual site dependence and external generalisation remain open; cluster blocking does not solve every leakage risk. | Viktor → Vladimir; analytics/evaluation consumers |
| Nominal capacity exceedance | B3, B4, B8 | Accepted VDR-01 records exceedance observations | Data/domain/product interpretation and explicit decision before use in risk logic; neither a defect nor a valid risk signal is established here | Viktor + Alisa → Vladimir; analytics, explanations and claims |

---

# 6. Shared-contract change triggers

Any proposed modification that alters the boundary between workstreams, changes public API contracts, or impacts external claims represents a **shared-contract change**.

No individual developer or automated agent may implement a shared-contract change locally. A formal integration gate (VLD-02 or equivalent human approval) is strictly required before changing:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   SHARED-CONTRACT CHANGE TRIGGERS                      │
│                                                                        │
│  1. Public RiskAssessment Contract: fields, nullability, enums         │
│  2. HTTP API Surface: routes, methods, request/response models         │
│  3. Canonical Input Model: BatchInput fields, validation, types        │
│  4. Prediction Semantics: changes to T_assess = T_dispatch boundary    │
│  5. Evaluation & Split Protocol: target choice, metric definitions     │
│  6. Domain Rules & Thresholds: adding active rules to domain_rules.md  │
│  7. Recommendation Meaning: action codes, priority, causal claims      │
│  8. Provenance & Tiering: engine_tier semantics, simulation flags      │
│  9. Application Persistence / Storage: storage layer, DB/ORM adoption │
│  10. System Dependencies: pyproject.toml, package.json, lockfiles      │
└────────────────────────────────────────────────────────────────────────┘
```

### Protection of sponsor prediction boundary ($T_{assess} = T_{dispatch}$)

The prediction boundary ($T_{assess} = T_{dispatch}$) is a higher-authority supplied challenge constraint. A VLD-02 decision cannot override it for technical convenience.

If newer authoritative challenge clarification changes it, the change procedure must:

1. **Surface the conflict:** Explicitly identify the discrepancy between the existing constraint and new sponsor guidance.
2. **Update canon and history:** Record the new authoritative clarification in `docs/challenge_canon.md` and document the requirement evolution.
3. **Reconsider internal decisions:** Formally re-evaluate dependent data contracts, feature definitions, and evaluation designs at an integration gate.

### Persistence vs deployment governance

- **Application persistence / storage:** ADR 0005 selects the initial separate JSON baseline artifact and loaded runtime context. Broader storage/database/registry needs remain unselected and require a further gate if needed.
- **Deployment / hosting:** Environment and platform selection remains under VLD-04 unless an earlier blocker requires a human decision. No hosting provider is preselected, and remote hosting does not require VLD-02 by default.

### Change gate procedure

When an owner discovers that a shared-contract change is necessary:

1. **STOP local implementation:** Do not modify the shared contract file.
2. **Prepare a Decision Packet (VLD-02 format):**
   - Exact problem and why existing contract is insufficient;
   - Cited evidence (from VDR, APR, or IGR);
   - Proposed exact diff/schema;
   - Impacted workstreams and files;
   - Alternatives considered and rejection rationale.
3. **Submit to Integrator (Vladimir):**
   - Integrator evaluates impact against challenge canon and existing guarantees.
   - Record the accepted decision in the appropriate canonical destination (`docs/decisions/<ADR>.md`, `docs/data_contract.md`, `docs/evaluation.md`, `docs/domain_rules.md`, `docs/architecture.md`, `docs/challenge_canon.md`, `docs/assumptions_unknowns.md`). Use an ADR when the decision is architectural or when an explicit durable decision record is useful.
4. **Coordinated Implementation:**
   - Producer and consumer contracts are updated synchronously with automated tests validating compatibility in subsequent bounded implementation tasks.

---

# 7. Integration STOP conditions

To protect the project from requirement drift, technical debt, and unjustified claims, all workstreams must immediately **STOP** and surface the issue when any of the following conditions occur:

1. **Unauthorized Contract Modification:** A task requires modifying `backend/app/domain/assessment.py`, `docs/data_contract.md`, or `frontend/src/api/contracts.ts` without an approved VLD-02 decision.
2. **Unverified Raw Field Behavior or Semantic Promotion:** Implementation code:
   - Relies on a dataset field not present in supplied challenge materials or accepted evidence;
   - Assumes unverified observed type, nullability, or referential integrity behavior;
   - Assigns unverified semantic meaning to raw columns;
   - Promotes a raw sponsor field into canonical or predictive semantics without the required evidence and decision gate.
3. **Unsourced Agronomic Thresholds:** A formula, threshold, or baseline rule uses hardcoded numbers (e.g. "temperature > 4°C is high risk") that have no approved entry in [`docs/domain_rules.md`](./domain_rules.md).
4. **Unsubstantiated Causal Claims:** A recommendation or factor description claims that taking an action will reduce loss by a specific percentage without validated empirical evidence.
5. **Leakage & Prediction Boundary Violation:** An analytics or feature engineering step accesses post-dispatch data (arrival checks, transit delays, destination outcomes) for predictive inference at $T_{dispatch}$.
6. **Contradiction Between Accepted Artifacts:** Two approved documents make incompatible assertions (e.g. data recon finds a table structure that invalidates an architecture assumption).
7. **Scope-Expanding Infrastructure Changes:** A pull request or task introduces external databases (PostgreSQL, Redis), Docker/Kubernetes requirements, message queues, or streaming protocols without explicit authorization.
8. **Untraceable Product Claims:** Pitch slides, README text, or UI labels make claims regarding accuracy, loss reduction, or scalability that cannot be traced to executed tests or evaluation reports.
9. **AI Self-Report as Verification:** An automated agent asserts that code or data is "verified" or "clean" without providing the exact executed commands, exit codes, and output snippets.
10. **Challenge Requirement Conflict:** New information or clarification indicates that an accepted team decision violates official challenge specifications.
11. **Local vs Committed State Confusion:** A task is initiated on a dirty repository base or confuses uncommitted local files with canonical repository state.
12. **Insufficient Evidence for Decision:** Pressure to make progress leads to deciding a model, target, or threshold while the underlying evidence remains classified as UNKNOWN.

When a STOP condition is triggered:
- The executor must halt work on the affected path immediately.
- Output a clear report starting with: `BLOCKED: <reason>`.
- Provide the exact file paths, diffs, or contradictions observed.
- Identify the specific human decision or missing evidence required to unblock.

---

# 8. Current blocked / unblocked dependency state

**History:** VLD-01 was prepared from `cafbcf832e7abb410ee9ff07954b4bb50e34aa81`, before the subsequent evidence deliveries. VLD-R1 reconciled the initial Layer-1 state at `54d233f1822f730a26fa225ec00d746e116875aa`. VLD-R2 reconciled post-VDR-02 evidence at `f9ca1d7bd29940e6b925884c7becae65dc921f7c`. The historical VLD-R3 reconciliation incorporated accepted, integrated VLD-02A (ADR 0002, PR #16), VDR-03 (PR #18), and APR-01 (PR #17) at `9cff00ce177f32dc2562d3458e0659281438d4c3`; it does not rewrite the earlier sequence or introduce unaccepted decisions.

**Historical state — VLD-APR-HG1R (2026-09-21):** At base `fb5d3a888474250a89d4eb1e06928ca9cd94f813`, ADR 0003 is ACCEPTED / INTEGRATED, PUX-08 is integrated as `DRAFT FOR REVIEW / NOT CANON` (PR #22; governed by ADR 0004 where applicable), IGR-02 raw ingestion/diagnostics is ACCEPTED / INTEGRATED (PR #21), IGR-03 canonical `BatchAssessmentInput` mapping is ACCEPTED / INTEGRATED (PR #28), and APR2-D1–D6 are formally ACCEPTED by Human Integrator Vladimir via [ADR 0004](./decisions/0004-mvp-product-scope.md) on 2026-09-21 (with source packets 08/09 remaining mixed research/specification artifacts). Earlier VLD-01/R1/R2/R3/02B/R4 history is preserved.

**Historical state — VLD-R5-HG1R (2026-09-22):** At `e8e14e3da7921a1d87f7bfc6e474f639ef87aa53`, Vladimir explicitly accepted HG-R5 D1–D7, recorded in ADR 0005. VLD-R5 remains reviewed evidence/decision packet, not wholesale canon.

**Historical state — VLD-R6 (2026-09-22):** At `794eac36b2deb7f244aeccc4ee2326100996edac`, RBS-01 is implemented and Human Integrated via PR #42 (commit `59cd759a1ac098475e553a6852505904f61341a7`). Artifact generator, versioned artifact, lifespan loader, single-batch assessment route `GET /api/v1/assessments/{batch_id}`, and health state synchronization are operational and verified in code. At that commit the frontend still consumed the synthetic demo.

**Current state — VLD-R8 / IGR05-D2R (2026-09-23):** PUX-11A real single-batch frontend lookup is implemented via PR #46. IGR-05B is **IMPLEMENTED / ACCEPTED / HUMAN INTEGRATED via PR #49**: the backend serves `GET /api/v1/assessments/{batch_id}` and `GET /api/v1/assessments`. `RiskAssessmentCollectionResponse` exists in both backend and frontend contracts. The collection endpoint applies the D2R default `2025-11-29T00:00:00Z <= dispatch_datetime < 2025-12-01T00:00:00Z` only when both bounds are omitted; explicit paired bounds remain configurable. It filters held-out candidates by dispatch window and optional facility, maps/scores the whole matching cohort, sorts by `risk.score DESC, batch_id ASC`, then slices by limit/offset. It returns the collection envelope and fails closed on mapping/scoring errors. The frontend ranked multi-batch queue is the next UX slice; no production deployment is claimed.

**DECISION — current shared semantic boundaries:** Under ADR 0003, dispatch ranking uses the offline `loss_fraction_pct` target and bounded severity score, with null risk band. A common ranked queue is restricted to one `engine_tier + engine_version`, ordered by `risk.score DESC`, then `batch_id ASC`. Different tiers/versions require separate comparability validation before mixing; fallback assessments must be separated or identified without a mixed ranked queue. Planned logistics remain optional/conditionally eligible under ADR 0002 and may be used by a future learned engine only if separately accepted; none is selected or required here. Horizon/recommendation stay null, reliability unavailable with null confidence, and factors factual or verified non-causal contributions (empty allowed). Engine-specific sufficiency must not invent blanket missingness/truncation rejection. Telemetry stays canonical; final learned subset remains open. D5 adopts the crop-conditioned training median baseline with global training median fallback for unseen crops, P1 primary, P2 mandatory robustness and P3 diagnostic-only; ≥15% remains evaluation relevance, not a production threshold.

### Initial deterministic-baseline runtime contract — ADR 0005

**IMPLEMENTED & ENFORCED IN CODE (RBS-01 / PR #42):** controlled offline fitting uses `dispatch_datetime < 2025-05-01` (900 Season-2024 batches); only `dispatch_datetime >= 2025-05-01` (900 held-out Season-2025 batches) is eligible for assessment. P1 membership is intentionally adopted for this initial artifact, not future production training policy. Requests never fit/refit; startup never silently fits all 1,800 outcomes. Future refits require an explicit release decision and distinct concrete engine version.

A separate validated JSON application artifact carries format version, algorithm/family identity, concrete engine_version, source_dataset_id, training partition identity, source table hashes, training-membership fingerprint, crop medians and global median. VDR-06A evidence JSON is not runtime state. Family: `baseline-crop-median-v1`; concrete version: `baseline-crop-median-v1-p1-s2024`; pinned assessment-source snapshot: `training-agrifood-snapshot-v1`. Exact artifact path/private arrangement remain implementation details.

FastAPI lifespan validates snapshot and artifact before publishing a complete context through an explicit provider. Analytics failure may leave health/demo reachable while real assessment is unavailable. No import-time/request-time fitting, automatic refitting, hot reload, background training or hidden regeneration. Accepted settings: `SMART_HARVEST_DATA_DIR`, `SMART_HARVEST_BASELINE_ARTIFACT`; defaults/path packaging remain implementation details. No extra required env variable is introduced. GET requires no expansion from `allow_methods=["GET"]`.

ADR 0005 D5 defines the no-body GET and backend-owned mapping; the client does not supply engine_version, source_dataset_id, generated_at, simulation or notice. Unknown IDs return 404; known training-cohort IDs return 409 (release eligibility, not queue membership or operational disposition); unavailable dataset/artifact or invalid/incompatible artifact returns 503; batch-specific canonical mapping/server-owned malformed source and unexpected internal failure return 500. These are not engine `insufficient_data`. Initial response policy: `Cache-Control: no-store`.

The initial runtime slice (offline artifact generation/validation, runtime loading, lifespan/provider, single-batch GET, health reconciliation and focused verification) is implemented in code and integrated via RBS-01 / PR #42. PUX-11A / PR #46 implemented frontend consumption of the real single-batch route. IGR-05B / PR #49 implemented backend multi-batch/replay serving, facility filtering, ranking and pagination. Frontend collection queue/presentation, database, learned/recommendation/deterioration engines, new confidence/minimum policy, comparability, background retraining, hot reload, deployment and VLD-03 remain deferred. If a valid canonical input cannot legitimately be assessed by the existing baseline: **STOP — HUMAN DECISION REQUIRED**. Dataset-backed simulation is not the synthetic fixture; fixture semantics remain unchanged and simulation=false remains outside HG-R5.

### Accepted evidence and decision state

| Workstream | Current state | Existing artifact | Integration evidence |
| --- | --- | --- | --- |
| VLD-01 | ACCEPTED / INTEGRATED | VLD-01 baseline of [integration_contract.md](./integration_contract.md) | [PR #6](https://github.com/Slave-of-Skynet/training_agrifood/pull/6) |
| VDR-01 | ACCEPTED / INTEGRATED | [01_dataset_inventory.md](./data_recon/01_dataset_inventory.md) | [PR #7](https://github.com/Slave-of-Skynet/training_agrifood/pull/7) |
| IGR-01 | ACCEPTED / INTEGRATED | [IGR-01-technical-recon.md](./recon/IGR-01-technical-recon.md) | [PR #8](https://github.com/Slave-of-Skynet/training_agrifood/pull/8) |
| PUX-00–07 | ACCEPTED / INTEGRATED AS RECON | [prscr_ux_demo_qa_report.md](../prscr_ux_demo_qa_report.md), at repository root | [PR #9](https://github.com/Slave-of-Skynet/training_agrifood/pull/9) |
| VDR-02 | ACCEPTED / INTEGRATED | [02_temporal_leakage.md](./data_recon/02_temporal_leakage.md) | [PR #14](https://github.com/Slave-of-Skynet/training_agrifood/pull/14) |
| VLD-02A / ADR 0002 | ACCEPTED DECISION / INTEGRATED | [0002-predictive-input-semantics.md](./decisions/0002-predictive-input-semantics.md) | [PR #16](https://github.com/Slave-of-Skynet/training_agrifood/pull/16) |
| VDR-03 | ACCEPTED / INTEGRATED | [03_target_horizon_feasibility.md](./data_recon/03_target_horizon_feasibility.md) | [PR #18](https://github.com/Slave-of-Skynet/training_agrifood/pull/18) |
| VDR-04A | ACCEPTED / INTEGRATED | [report](./data_recon/04_dispatch_predictability.md), [results JSON](./data_recon/04_dispatch_predictability_results.json) | [PR #20](https://github.com/Slave-of-Skynet/training_agrifood/pull/20) |
| VLD-02B / ADR 0003 | ACCEPTED HUMAN DECISION / INTEGRATED | [ADR 0003](./decisions/0003-assessment-evaluation-semantics.md), D1–D10 with D3/D4 overrides | Integrated (PR #21 base) |
| IGR-02 | ACCEPTED / INTEGRATED | Raw reader, manifest, and diagnostics (`backend/app/ingestion/`) | [PR #21](https://github.com/Slave-of-Skynet/training_agrifood/pull/21) |
| PUX-08 | INTEGRATED AS DRAFT FOR REVIEW / NOT CANON | [PUX-08-data-ux-reconciliation.md](./recon/PUX-08-data-ux-reconciliation.md) | [PR #22](https://github.com/Slave-of-Skynet/training_agrifood/pull/22) |
| IGR-03 | ACCEPTED / INTEGRATED | Canonical `BatchAssessmentInput` & mapper (`backend/app/domain/batch.py`, `backend/app/ingestion/canonical_mapper.py`) | [PR #28](https://github.com/Slave-of-Skynet/training_agrifood/pull/28) |
| IGR-04A / IGR-04B | IMPLEMENTED INTERNALLY | `backend/app/analytics/crop_median_baseline.py`, `backend/app/services/baseline_assessment.py` | Committed reference base `e8e14e3da7921a1d87f7bfc6e474f639ef87aa53` |
| VLD-R5 / HG-R5 / ADR 0005 | Reviewed RECON evidence; ACCEPTED HUMAN DECISION | [VLD-R5](./recon/VLD-R5-runtime-assessment-path-recon.md), [ADR 0005](./decisions/0005-runtime-baseline-serving.md) | Explicit Human acceptance 2026-09-22; ADR 0005 authoritative |
| RBS-01 | ACCEPTED / IMPLEMENTED / HUMAN INTEGRATED | `scripts/generate_baseline_artifact.py`, `backend/artifacts/`, `backend/app/runtime/`, `backend/app/api/routes.py`, `backend/tests/test_runtime_baseline.py` | [PR #42](https://github.com/Slave-of-Skynet/training_agrifood/pull/42), merge commit `794eac36b2deb7f244aeccc4ee2326100996edac` |
| PUX-11A | ACCEPTED / IMPLEMENTED / INTEGRATED | Real single-batch frontend lookup through `GET /api/v1/assessments/{batch_id}` | [PR #46](https://github.com/Slave-of-Skynet/training_agrifood/pull/46) |
| IGR-05A / D1–D10 / D2R | ACCEPTED HUMAN DECISION | [IGR-05A recon and D2R amendment](./recon/IGR-05A-multi-batch-serving-recon.md) | D1–D10 accepted 2026-09-22; D2R accepted 2026-09-23 |
| IGR-05B | ACCEPTED / IMPLEMENTED / HUMAN INTEGRATED | Backend collection route, service, tests and synchronized `RiskAssessmentCollectionResponse` | [PR #49](https://github.com/Slave-of-Skynet/training_agrifood/pull/49) |
| APR-01 (steps 0–5) | DELIVERED / INTEGRATED / ACCEPTED RESEARCH EVIDENCE | [`docs/product_recon/`](./product_recon/) | [PR #17](https://github.com/Slave-of-Skynet/training_agrifood/pull/17) |
| APR-02F / ADR 0004 | ACCEPTED HUMAN DECISION (ADR 0004) on 2026-09-21 (APR2-D1–D6 accepted; 08/09 source artifacts remain mixed research/spec) | [ADR 0004](./decisions/0004-mvp-product-scope.md), [08_mvp_scope_decision_packet.md](./product_recon/08_mvp_scope_decision_packet.md), [09_product_acceptance_traceability.md](./product_recon/09_product_acceptance_traceability.md) | [PR #29](https://github.com/Slave-of-Skynet/training_agrifood/pull/29), ADR 0004 |

Acceptance of a research/report artifact does not adopt all its recommendations as DECISION or prove implementation. APR-01 research documents retain their own epistemic labels (`FACT`, `DOMAIN FACT`, `INFERENCE`, `UNKNOWN`, `NOT CANON`) and are not automatically challenge canon as a whole. PUX-08 is integrated as draft evidence, not accepted product canon (though governed by ADR 0004 where applicable). Decisions APR2-D1–D6 were formally accepted by Human Integrator Vladimir via ADR 0004 on 2026-09-21; the source documents (08 and 09) remain mixed research/spec artifacts. IGR-01 records historical backend verification and host-specific runtime/build limitations; PUX distinguishes planned QA from executed checks. No fresh application verification is claimed by this documentation update.

### Readiness under existing task-specific gates

| Work | Current readiness | Required next evidence / gate |
| --- | --- | --- |
| Bounded raw-only IGR-02 | **COMPLETE / ACCEPTED / INTEGRATED** through [PR #21](https://github.com/Slave-of-Skynet/training_agrifood/pull/21) | Ingestion diagnostics operational in code; external schema generalisation remains open |
| VDR-02 | **COMPLETE / ACCEPTED / INTEGRATED** through [PR #14](https://github.com/Slave-of-Skynet/training_agrifood/pull/14) | Prerequisite satisfied; evidence consumed by VLD-02 gate and subsequent D&E tasks |
| VDR-03 | **COMPLETE / ACCEPTED / INTEGRATED** through [PR #18](https://github.com/Slave-of-Skynet/training_agrifood/pull/18) | Target/horizon evidence prerequisite satisfied; VDR-04A accepted and ADR 0003 adopts bounded semantics. No model or onset implementation follows automatically |
| APR-01 (steps 0–5) | **DELIVERED / INTEGRATED / ACCEPTED RESEARCH EVIDENCE** through [PR #17](https://github.com/Slave-of-Skynet/training_agrifood/pull/17) | Research notes retain FACT/DOMAIN FACT/INFERENCE/UNKNOWN/NOT CANON labels; does not automatically make research canon as a whole |
| PUX-08 | **INTEGRATED AS DRAFT FOR REVIEW / NOT CANON** through [PR #22](https://github.com/Slave-of-Skynet/training_agrifood/pull/22) | Research evidence artifact; candidate workflows and recommendations remain gated and not authoritative by themselves |
| VLD-02A / IGR-03 predictive input | **COMPLETE / ACCEPTED / INTEGRATED** through [PR #28](https://github.com/Slave-of-Skynet/training_agrifood/pull/28) | Typed canonical `BatchAssessmentInput` domain models and deterministic raw-to-canonical mapper are operational in code/tests. IGR-04A/04B and RBS-01 implement scoring/assessment and single-batch serving. |
| VLD-02B / ADR 0003 | **ACCEPTED HUMAN DECISION; INTEGRATED** | Assessment, ranking, baseline, and evaluation semantics accepted |
| APR-02F product spec / ADR 0004 | **ACCEPTED HUMAN DECISION (ADR 0004)** on 2026-09-21 | Human Integrator (Vladimir) accepted APR2-D1–D6 via ADR 0004; source artifacts 08/09 remain mixed research/spec |
| Bounded deterministic baseline serving (RBS-01) | **COMPLETE / ACCEPTED / INTEGRATED** through [PR #42](https://github.com/Slave-of-Skynet/training_agrifood/pull/42) | Single-batch GET route, artifact lifecycle, lifespan context, and health synchronization operational in code; frontend lookup followed in PUX-11A / PR #46 |
| IGR-05A / D1–D10 / D2R | **ACCEPTED HUMAN DECISION** | D2R supersedes only omitted-bounds default; strict paired bounds and D1/D3–D10 remain accepted |
| IGR-05B | **ACCEPTED / IMPLEMENTED / HUMAN INTEGRATED** through [PR #49](https://github.com/Slave-of-Skynet/training_agrifood/pull/49) | Backend collection serving, shared response contract, replay window, facility filter, global ranking, limit/offset and fail-closed behavior implemented; frontend queue remains next UX slice |
| Bounded analytics-engine planning | **CONCEPTUALLY UNBLOCKED** | Production learned engine/model unselected and not required; separate acceptance before use |
| Evaluation harness |
| VDR-06A COMMITTED / PARITY PASS |
| P1/P2 application-baseline parity harness implemented;
  evidence retains its own status qualifier and is not canon by itself.
  Future learned-engine evaluation remains separate work. |
| UX reconciliation | **CONCEPTUALLY UNBLOCKED** for accepted semantics | Existing PUX sequence, same-tier/version queue restriction, null/unavailable outputs; no frontend implementation here |
| Unsupported analytical/claim capabilities | **STILL BLOCKED / INTENTIONALLY UNSUPPORTED** | Exact countdown, risk bands, confidence percentages, causal interventions, savings, final production model selection and automatic mixed-tier/version ranking need separate evidence/gates |
| Final interactive dashboard | **BLOCKED** on its existing implementation prerequisites | Assessment endpoints/contracts, reconciled UX and supported data/product semantics |
| VLD-03 / VLD-04 / VLD-05 | **BLOCKED** on their respective integration, runtime and claims prerequisites | Working backend/frontend plus evaluation evidence → stable reproducible demo → traceable claims |

**Raw and canonical ingestion boundary:** IGR-02 and IGR-03 are implemented and tested. They do **not** authorize or implement production analytics scoring, predictive eligibility decisions beyond ADR 0002, feature transformations, imputation/exclusion policy, or recommendation logic.

---

# 9. Traceability rules

Every feature, formula, metric, and public statement in Smart Harvest must follow an unbroken, auditable trail from evidence to output.

Rather than forcing all work through a single rigid linear sequence, the traceability model branches based on whether an integration boundary or shared contract is affected:

```text
Evidence
  │  (Sponsor data profiling, domain literature, mentor clarification)
  ▼
Does it require a new or changed shared decision?
  │
  ├─► YES ──► Relevant Human Integration Gate (such as VLD-02)
  │             │
  │             ▼
  │           Canonical / Shared Contract Update
  │             │  (docs/data_contract.md, app/domain/, frontend contracts)
  │             ▼
  │           Bounded Implementation Contract
  │             │  (Scoped write branch, task-specific PR)
  │             ▼
  │           Verification
  │              (Automated tests, contract compatibility checks)
  │
  └─► NO  ──► Existing Accepted Contract
                │
                ▼
              Bounded Implementation Task
                │  (Local code within agreed technical scope)
                ▼
              Verification
                 (pytest, npm test, lint, local tests)

Verified Product Behavior / Evaluation Evidence
  │
  ▼
VLD-05 Final Consistency & Pitch Claim Gate
  │  (Audit against reproducible evidence, canon, and test results)
  ▼
Final Solution & Truthful Pitch Presentation
```

### Local implementation vs shared-contract gates

- **Local implementation within accepted contracts does not require VLD-02:** Workstream owners may implement internal logic, algorithms, helper functions, tests, and UI components that strictly conform to existing accepted contracts and boundaries without triggering an integration gate.
- **Shared-contract changes require VLD-02:** When an evidence finding necessitates altering a boundary, adding or modifying public model fields, redefining input semantics, or introducing architectural dependencies, the change must pass through a formal human integration gate (such as VLD-02) before downstream implementation begins.
- **Pitch claims pass VLD-05 rather than VLD-02:** Pitch deck assertions, README statements, and demo claims do not pass through VLD-02. All claims regarding model performance, loss reduction, operational impact, or system capabilities must pass through the **VLD-05 Final Consistency & Pitch Claim Gate**, where they are audited directly against verified product behavior and reproducible evaluation evidence.

### Verification standards

1. **No Phantom Verification:** Assertions that code "works" or tests "pass" must include the exact command executed, exit status, and console output summary.
2. **Synthetic Data Quarantine:** Synthetic fixtures and demo stubs must permanently carry `simulation: true` and the notice `SIMULATION / synthetic fixture / not challenge data`. They may never be substituted for evaluation data.
3. **Auditability:** Every metric cited in the pitch or README must be reproducible by running an inspection command or script from a clean repository state.
4. **History Preservation:** When new evidence invalidates an earlier assumption, the change must be recorded as an evolution of requirements, not by silently editing commit history or pretending the earlier state never existed.

---

# 10. Current limitations

The original VLD-01 limitations are reconciled below against accepted evidence and ADRs 0003–0005; accepted semantics are distinguished from absent implementation:

1. **Raw Ingestion Logic Implemented (IGR-02):** Raw CSV reading, table specifications, and physical structural integrity verification are implemented and tested in `backend/app/ingestion/` (PR #21). Unseen schema handling and general external repair policies remain open.
2. **Deterministic Baseline Serving and Backend Multi-Batch Collection Implemented:** IGR-03 maps canonical inputs, IGR-04A fits/scores, IGR-04B constructs RiskAssessment, RBS-01 serves single-batch assessments via `GET /api/v1/assessments/{batch_id}` (PR #42), and IGR-05B serves ranked collections via `GET /api/v1/assessments` (PR #49). The collection uses a configurable half-open dispatch window, optional facility filtering, rank-before-slice pagination, and fail-closed assessment. Learned models and recommendation engines remain deferred.
3. **Single-Batch Frontend Implemented; Ranked Queue Frontend Deferred:** PUX-11A (PR #46) integrated real single-batch assessment lookup through `GET /api/v1/assessments/{batch_id}` with HTTP 404/409/503 feedback. The frontend does not yet consume or render the collection endpoint. Backend multi-batch serving is implemented; multi-batch frontend queue/presentation is not implemented.
4. **Null Horizon Policy Accepted:** ADR 0003 requires null horizon for current engines; exact onset remains unsupported. No timing prediction is implemented.
5. **No Active Agronomic Rules:** The domain rule register ([`docs/domain_rules.md`](./domain_rules.md)) remains empty of validated active rules.
6. **No Production Learned Model Selected or Required:** VDR-04A trained feasibility benchmarks; ADR 0003 accepts P1/P2/P3 policy and a deterministic baseline. Neither HGB nor another learned family/hyperparameters is selected for production.
7. **Baseline Artifact Implemented; Broader Persistence Undecided:** A versioned JSON application artifact (`backend/artifacts/baseline-crop-median-v1-p1-s2024.json`) and lifespan loading are implemented for the initial baseline release (RBS-01). Broader production persistence, external databases, ORMs, or model registry services remain undecided.
8. **No Remote Deployment Selected:** No remote deployment platform or hosting provider is preselected. Environment and platform selection remains under VLD-04 unless an earlier blocker requires a human decision. The current foundation demo runbook describes local execution.
