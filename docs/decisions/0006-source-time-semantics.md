# ADR 0006 — Source Timestamp Semantics Correction

- **Status:** Accepted
- **Decision Owner:** Vladimir (Integrator)
- **Date:** 2026-09-23
- **Decision source:** TEMP-D1–D5 (Human Gate)
- **Task:** TEMP-R1 — Sponsor Timestamp Semantics Correction

---

## 1. Context

`sponsor_pack/README.md` §4 explicitly defines the physical temporal coordinate standard for the challenge dataset:

> Timestamps are local Moldova time on a continuous UTC+3 timeline and are formatted as `YYYY-MM-DD HH:MM:SS`.

Raw dataset CSV files in `sponsor_pack/data/` provide timestamps as offset-free strings (e.g. `2025-11-29 12:00:00`), which represent local wall-clock time on this continuous UTC+3 timeline (`2025-11-29T12:00:00+03:00`), not UTC (`2025-11-29T12:00:00Z`).

At starting base (`65c09bee122cc068866a9cb2e1cac32e9edc7118`), the multi-batch collection serving implementation in `backend/app/services/collection_assessment.py` used a helper named `_utc_clock()` that assigned `timezone.utc` directly to naive datetimes, converted aware API boundaries to UTC, and defined default replay window constants using UTC (`datetime(2025, 11, 29, tzinfo=timezone.utc)` to `datetime(2025, 12, 1, tzinfo=timezone.utc)`). This turned sponsor wall-clock values into incorrect UTC instants (shifting them physically by 3 hours).

During multi-agent frontend reconnaissance (FE-RECON-A) prior to implementing UI replay controls, this semantic discrepancy was identified. Crucially, empirical verification confirmed that the accepted Nov 29–Dec 1 D2R default replay cohort contains the exact same 18 eligible held-out batches under the corrected source-time interpretation. Therefore, correcting the serving clock reconciles the implementation with official sponsor package documentation without altering the chosen demo cohort.

---

## 2. Decisions

### TEMP-D1 — Source timestamp semantics
Sponsor dataset timestamps without an offset are interpreted as fixed source-local:

```text
UTC+03:00
```

for this training snapshot. A fixed UTC+03 offset is used. The implementation must **not** substitute a DST-sensitive runtime timezone policy (such as an inferred `Europe/Chisinau` zoneinfo rule), because the official source explicitly defines its timeline as continuous UTC+3 throughout active harvest and storage.

### TEMP-D2 — Collection comparison clock
All timestamps compared by collection serving must be normalized to the same fixed source clock:

```text
UTC+03:00
```

Normalization rules:
1. **Naive source datetime:** A raw timestamp string such as `2025-11-29 12:00:00` attaches fixed `UTC+03:00` without shifting wall clock, becoming `2025-11-29T12:00:00+03:00`.
2. **Naive explicit API boundary:** A query parameter boundary without an offset (e.g. `2025-11-29 12:00:00` or `2025-11-29T12:00:00`) is interpreted as source-local `2025-11-29T12:00:00+03:00`.
3. **Aware explicit API boundary:** Any aware datetime is converted to the source clock (`astimezone(SOURCE_TIMEZONE)`) while strictly preserving its physical instant. Thus, the following describe the exact same physical instant:
   - `2025-11-29T12:00:00+03:00` (source-local)
   - `2025-11-29T09:00:00Z` (UTC equivalent)
   - `2025-11-29T11:00:00+02:00` (EET equivalent)

### TEMP-D3 — Default replay window
The D2R calendar-window intent is preserved:

```text
2025-11-29T00:00:00+03:00 <= dispatch_datetime < 2025-12-01T00:00:00+03:00
```

Duration remains 48 hours. Equivalent UTC instants:

```text
2025-11-28T21:00:00Z <= instant < 2025-11-30T21:00:00Z
```

The collection response must expose effective boundaries with the correct `+03:00` offset rather than falsely labelling source-local midnight as `Z`. The pinned default cohort remains 18 eligible batches.

### TEMP-D4 — Explicit naive API boundaries
Naive query parameters remain accepted and are interpreted as source-local UTC+03 rather than being rejected. This task does **not** introduce a new HTTP `400` requirement for missing timezone offsets. The existing paired-boundary requirement (both boundaries required together or both omitted) remains unchanged.

### TEMP-D5 — Correction boundary
This task corrects the collection-serving temporal boundary only. It must **not** expand into a repository-wide datetime migration. Specifically, the following remain unchanged:
- raw CSV representations in `sponsor_pack/data/`;
- canonical Pydantic schemas in `backend/app/domain/`;
- canonical mapper output structure in `backend/app/ingestion/canonical_mapper.py`;
- training / held-out partition membership in `backend/app/runtime/artifact.py`;
- artifact cutoff (`CUTOFF = datetime(2025, 5, 1)`);
- baseline scoring;
- queue ranking (`risk.score DESC, batch_id ASC`);
- facility filter semantics;
- pagination;
- single-batch endpoint (`GET /api/v1/assessments/{batch_id}`);
- frontend source code.

---

## 3. Consequences

- **Instant correctness:** Collection window comparisons become instant-correct, properly comparing physical points in time.
- **Naive query compatibility:** Naive query bounds cleanly map to source-local UTC+03 without breaking client ergonomics.
- **Aware query normalization:** Aware query bounds with any valid offset (e.g. `Z`, `+02:00`, `+03:00`) are normalized to source clock while preserving physical instant.
- **Effective boundary serialization:** Collection response fields `window_start` and `window_end` serialize with explicit `+03:00` offset strings (e.g. `2025-11-29T00:00:00+03:00`).
- **Preserved D2R intent and cohort:** The default replay window remains Nov 29–Dec 1 source-local wall clock (48 hours), and the pinned default cohort remains identical (18 batches, headed by `BAT-000910`).
- **No algorithmic changes:** Ranking, scoring, and partition membership remain identical.
- **Bounded footprint:** No broad repository migration or new dependency was introduced.

---

## 4. Negative Boundary

ADR 0006 explicitly does **NOT** claim:
- that all future Moldovan datasets use fixed continuous UTC+3;
- that real Moldova civil time never observes Daylight Saving Time (DST);
- that generalized production timezone handling across arbitrary jurisdictions is solved;
- that every canonical datetime field across all domain models has been migrated to timezone-aware datetimes.

This decision addresses source-specific temporal semantics strictly for the supplied training challenge snapshot in multi-batch collection serving.
