# ADR 0007 — Frontend Ranked Queue UX

Status: Accepted  
Date: 2026-09-23  
Decision Owner: Vladimir (Integrator)  
Decision source: FE-D1–FE-D6 Human Gate  
Task: PUX-12A

## Accepted decisions

- **FE-D1:** Use a queue-first master/detail desktop workspace. On mobile, stack priority queue → batch detail → single-batch lookup → system status.
- **FE-D2:** Automatically load `GET /api/v1/assessments` only when health reports `analytics: ready`. Do not poll.
- **FE-D3:** Preserve backend collection order. Show no ordinal ranks. Equal severity scores are ties; Batch ID only makes their order deterministic.
- **FE-D4:** Selecting a queue item sends its complete collection `RiskAssessment` directly to the existing detail card. Manual Batch ID lookup remains a real `GET /api/v1/assessments/{batch_id}`. Do not initially select a batch.
- **FE-D5:** The first frontend slice has no filters, replay-window controls, or pagination.
- **FE-D6:** Queue rows show Batch ID and four-decimal predicted loss severity score. Display the returned simulation notice prominently. The score is for prioritisation, not a probability, confidence score, or guarantee of loss. Do not add bands or action controls.

The current collection response lacks per-row crop, facility, dispatch, and storage metadata. Adding those fields requires a future shared-contract gate.
