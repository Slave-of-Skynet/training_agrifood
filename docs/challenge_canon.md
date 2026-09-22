# Challenge canon

## Status and scope

**FACT:** Smart Harvest: Reduce Post-Harvest Losses is a **SIMULATION / training challenge** for the SoS AgriFood team. It is not evidence of a real provider requirement or a production commitment.

**FACT:** The repository now contains the supplied training challenge materials under `sponsor_pack/`: the challenge brief, sponsor README, eight relational CSV tables, and `sponsor_pack/data/data_dictionary.xlsx`.

**FACT:** Those supplied materials document a relational source structure, declared field names and types, dispatch-time assessment semantics (`T_assess = T_dispatch`), historical outcome fields, and a public/hidden temporal restriction. This records what the training package supplies; it is not evidence about a real GigaHack provider or real commercial operations.

**FACT:** For predictive assessment, only information available at dispatch is eligible. Arrival inspection, actual post-dispatch delay or incidents, post-dispatch telemetry unavailable at assessment, final outcomes, and equivalent future observations are forbidden prediction inputs. Their presence in public historical files permits retrospective analysis, not inference-time use.

**FACT — accepted snapshot inventory evidence:** [VDR-01](data_recon/01_dataset_inventory.md), accepted and integrated through [PR #7](https://github.com/Slave-of-Skynet/training_agrifood/pull/7), empirically inspected the supplied snapshot. It established observed schemas/types, row counts and file sizes, PK/FK integrity, observed relationships/cardinalities, sampling/coverage characteristics, missingness and selected data-quality anomalies, and crop/cultivar and historical outcome coverage. These findings update the earlier pre-profiling state; they do not guarantee the same structure or quality in future data.

**FACT — accepted snapshot temporal/leakage evidence:** [VDR-02](data_recon/02_temporal_leakage.md), accepted and integrated through [PR #14](https://github.com/Slave-of-Skynet/training_agrifood/pull/14), audited temporal chronology, assessment boundaries, and leakage risks. Across all 1,800 batches, observed physical events follow an ordered physical actual-event sequence with 0 sequence violations: $T_{harvest} < T_{harvest\_qc} < T_{entry} < T_{pre\_dispatch\_qc} < T_{dispatch} \le T_{actual\_departure} < T_{actual\_arrival} = T_{arrival\_qc}$. The prediction cutoff boundary is $T_{assess} \equiv T_{dispatch} = \text{storage_sessions.dispatch_datetime}$. Pre-dispatch features (intake descriptors, storage session context, zone/facility specifications, harvest and pre-dispatch quality checks) are physically available prior to release, while post-dispatch fields (arrival QC, actual departure/arrival/delay, in-transit telemetry and incidents, destination outcomes) represent severe future/target leakage and are strictly forbidden prediction inputs. Telemetry logging terminates globally on 2025-12-31 23:30:00, leaving 204 batches (11.33%, primarily apples and pears) dispatched in 2026 with pre-dispatch telemetry gaps of 0.56 to 92.54 days, while non-truncated batches exhibit maximum staleness of 29.4 minutes at dispatch. 1,734 of 1,800 batches (96.33%) concurrently share storage chambers, forming 157 disjoint chamber-time clusters; in standard randomized 80/20 train/test splits, an average of 95.79% of test batches share an identical chamber microclimate cluster with training batches, while naive chronological 70/30 splitting causes complete disappearance of summer crops from the test partition.

**FACT — source timestamp standard:** The supplied sponsor package declares offset-free timestamps to represent local Moldova time on a continuous UTC+3 timeline.

**DECISION — ADR 0006:** collection replay boundaries normalize source and API timestamps against the fixed UTC+03 source clock.

**DECISION — accepted predictive-input semantics (ADR 0002 / VLD-02A):** [ADR 0002](decisions/0002-predictive-input-semantics.md), accepted under VLD-02A through [PR #16](https://github.com/Slave-of-Skynet/training_agrifood/pull/16), established canonical predictive-input semantics for dispatch-time assessment ($T_{assess} \equiv T_{dispatch}$). It defined canonical entity boundaries, authoritative identity sources, a 73-field eligibility taxonomy, strict exclusion of arrival/in-transit/outcome leakage, bounding of telemetry to storage stay ($T_{entry} \le t \le T_{dispatch}$), explicit missingness / zero-fabrication rules, and the canonical `BatchAssessmentInput` specification. It does not establish production analytics scoring runtime, feature-engineering windows, target, metric, evaluation split, runtime deterioration-horizon policy, risk formula, baseline/model, reliability policy, or action effects.

**FACT — implemented canonical input mapping (IGR-03):** Integrated through [PR #28](https://github.com/Slave-of-Skynet/training_agrifood/pull/28), IGR-03 implements the committed canonical `BatchAssessmentInput` data model (`backend/app/domain/batch.py`) and deterministic raw-to-canonical mapper (`backend/app/ingestion/canonical_mapper.py`) for the supplied training snapshot and accepted ADR 0002 semantics. It verifies authoritative entity joins and fail-closed cardinalities, enforces dispatch-time cutoffs ($T_{assess} \equiv T_{dispatch}$), strictly excludes post-dispatch and outcome leakage fields, restricts telemetry to storage stay ($T_{entry} \le t \le T_{dispatch}$), preserves structural missingness as `None`, and maps planned logistics fields. This implements canonical input extraction for the supplied training snapshot; it does not establish production analytics scoring, runtime crop-median evaluation, recommendation generation, multi-batch queue endpoints, or generalized production-data behaviour outside the supplied snapshot.

**FACT — accepted target and deterioration-horizon feasibility evidence (VDR-03):** [VDR-03](data_recon/03_target_horizon_feasibility.md), accepted and integrated through [PR #18](https://github.com/Slave-of-Skynet/training_agrifood/pull/18), profiled candidate outcomes and deterioration timing. Four complete historical candidate outcome fields exist for all 1,800 batches in `historical_quality_outcomes.csv`: `quality_status`, `loss_fraction_pct`, `quality_score`, and `economic_loss_eur`. `quality_status` is reproduced by observed `loss_fraction_pct` intervals ($[0,5)\%$, $[5,15)\%$, $[15,35)\%$, $[35,100]\%$) with zero mismatches in the supplied snapshot. `economic_loss_eur` is deterministically reproduced from loss fraction $\times$ harvest weight $\times$ inferred crop unit price. `quality_score` is strongly correlated ($r = -0.9727$) with `loss_fraction_pct`, but its exact generation rule remains undocumented. Quality inspections occur at exactly three discrete checkpoints per batch (`harvest`, `pre_dispatch`, `arrival`); no intermediate quality inspections exist during storage or transit. No exact deterioration-onset timestamp is observed.

**INFERENCE / evidence conclusion:** Exact continuous deterioration timing is not supportable from the current observations.

**FACT / OBSERVED RESULT — accepted VDR-04A evidence:** [VDR-04A](data_recon/04_dispatch_predictability.md) and its [results](data_recon/04_dispatch_predictability_results.json) are ACCEPTED / INTEGRATED through [PR #20](https://github.com/Slave-of-Skynet/training_agrifood/pull/20). Point prediction has limited/context-specific, metric-dependent lift. Ranking lift exists; the planned-logistics family produced the strongest and most consistent incremental association among tested feature families. Ranking without logistics is protocol/model-dependent, not impossible. Tested telemetry aggregates did not demonstrate stable material marginal lift. The experiment did not separately test context plus logistics without telemetry, establish causal effects or select a production model.

**DECISION — ADR 0003:** Vladimir approved [assessment, ranking and evaluation semantics](decisions/0003-assessment-evaluation-semantics.md) on 2026-09-20, with explicit D3/D4 overrides. The primary task is dispatch-time batch prioritisation, using `loss_fraction_pct` as the offline supervised label only. `risk.score = clip(predicted_loss_fraction_pct, 0, 100) / 100` is a severity score, not probability/confidence; `risk.band = null`. Order assessed batches by score descending and `batch_id` ascending, only within one `engine_tier + engine_version`; different tiers/versions must not be automatically mixed before separate comparability validation. Fallback assessments must be separated or identified, without a mixed ranked queue. Planned logistics remain optional / conditionally eligible under ADR 0002 and may be used by a future learned engine only if separately accepted; no production learned engine is selected or required.

**DECISION — current output and evaluation policy:** Horizon and recommendation remain null; reliability is `unavailable` with null confidence. Sufficiency depends on the selected engine's declared minimums, without automatic rejection for optional channel missingness or telemetry truncation. Factors may be factual conditions or verified model contributions, never fabricated causal explanations; an empty list is allowed. P1 forward inter-season is primary, P2 chamber-time grouped OOF is mandatory robustness, and P3 random splitting is a non-defensible diagnostic. The deterministic baseline uses crop-conditioned training median loss with global training median fallback for an unseen crop. Ranking is prioritisation, not exhaustive screening. The ≥15% boundary remains evaluation-only. Telemetry stays in canonical inputs; final learned features require later evaluation. These decisions define semantics, not implemented capability.

**UNKNOWN / decisions still required:** Future/unseen schema deviations and generalized production-data behaviour outside the supplied snapshot; engine minimums, fallback routing and cross-tier/version comparability; feature transformations/windows and final learned subset; production learned engine/model family/hyperparameters; staleness and imputation/repair policies; confidence calibration, band/alert and agronomic thresholds; biological onset; explanation validation; operator persona, authority, queue/workflow and capacity; action availability/effects/costs/lead times and financial savings; label/business provenance, external generalisation and residual site dependence; hosting, persistence, runtime resources, realtime needs and capacity-exceedance interpretation. See the [global register](assumptions_unknowns.md). Historical outcome relationships do not establish deterministic prediction or causal loss reduction.

## Required operator outcomes

The intended product should help an operator understand:

1. which batches are most at risk;
2. when quality may begin to deteriorate;
3. which factors contribute to the risk;
4. which action should be prioritized to reduce losses.

These are desired challenge outcomes, not proof that the present foundation computes them. The current synthetic response reports `insufficient_data`.

## Evaluation criteria

- Agricultural and business usefulness.
- Accuracy and reliability.
- Usability and explainability.
- Potential reduction of food loss.
- Scalability.
- Innovation.

**DECISION:** ADR 0003 adopts the task, offline target, deterministic baseline and evaluation metric/protocol package. Numerical acceptance targets, operational thresholds and business/loss-reduction claims remain **UNKNOWN**; benchmark evidence is not a production performance guarantee.

## Canon rule

Every future claim must be classified:

- **FACT** — directly supported by supplied challenge material or validated evidence.
- **DECISION** — an explicit engineering/product choice with recorded rationale.
- **UNKNOWN** — unresolved and not safe to treat as fact.

Assumptions used for experiments must remain visibly labeled and must not silently enter production semantics.
