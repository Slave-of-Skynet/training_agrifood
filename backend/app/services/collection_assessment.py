"""Bounded held-out assessment collection using the canonical baseline path."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.domain.assessment import RiskAssessmentCollectionResponse
from app.ingestion.canonical_mapper import build_batch_assessment_input
from app.runtime.artifact import DATASET_ID, ENGINE_VERSION, NOTICE
from app.runtime.context import AnalyticsRuntimeContext
from app.services.baseline_assessment import build_baseline_assessment

SOURCE_TIMEZONE = timezone(timedelta(hours=3))

DEFAULT_WINDOW_START = datetime(2025, 11, 29, tzinfo=SOURCE_TIMEZONE)
DEFAULT_WINDOW_END = datetime(2025, 12, 1, tzinfo=SOURCE_TIMEZONE)


class InvalidWindowError(ValueError):
    """The supplied replay boundaries do not form a valid window."""


class FacilityNotFoundError(ValueError):
    """The requested facility is absent from the accepted snapshot."""


def _source_clock(value: datetime) -> datetime:
    """Normalize timestamps to the fixed continuous UTC+03 source clock."""
    if value.tzinfo is None:
        return value.replace(tzinfo=SOURCE_TIMEZONE)
    return value.astimezone(SOURCE_TIMEZONE)


def get_assessment_collection(
    runtime: AnalyticsRuntimeContext,
    *,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
    facility_id: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> RiskAssessmentCollectionResponse:
    """Score every matching candidate, then rank globally before pagination."""
    if (window_start is None) != (window_end is None):
        raise InvalidWindowError("Both window boundaries are required together")
    start = _source_clock(window_start) if window_start is not None else DEFAULT_WINDOW_START
    end = _source_clock(window_end) if window_end is not None else DEFAULT_WINDOW_END
    if start >= end:
        raise InvalidWindowError("window_start must be before window_end")

    snapshot = runtime.snapshot
    if facility_id is not None and facility_id not in {
        row["facility_id"] for row in snapshot["facilities"].rows
    }:
        raise FacilityNotFoundError(facility_id)

    zone_facilities = {
        row["zone_id"]: row["facility_id"]
        for row in snapshot["storage_zones"].rows
    }
    candidate_ids = []
    for session in snapshot["storage_sessions"].rows:
        batch_id = session["batch_id"]
        if batch_id not in runtime.held_out_ids:
            continue
        dispatch = _source_clock(datetime.fromisoformat(session["dispatch_datetime"]))
        if not start <= dispatch < end:
            continue
        if facility_id is not None and zone_facilities[session["zone_id"]] != facility_id:
            continue
        candidate_ids.append(batch_id)

    generated_at = datetime.now(timezone.utc)
    assessments = []
    for batch_id in candidate_ids:
        batch_input = build_batch_assessment_input(snapshot, batch_id)
        assessments.append(build_baseline_assessment(
            runtime.baseline,
            batch_input,
            engine_version=ENGINE_VERSION,
            generated_at=generated_at,
            source_dataset_id=DATASET_ID,
            simulation=True,
            notice=NOTICE,
        ))
    if any(item.risk is None for item in assessments):
        raise ValueError("Baseline assessment has no risk score")
    assessments.sort(key=lambda item: (-item.risk.score, item.batch_id))

    return RiskAssessmentCollectionResponse(
        items=assessments[offset:offset + limit],
        total_count=len(assessments),
        window_start=start,
        window_end=end,
        facility_id=facility_id,
        engine_version=ENGINE_VERSION,
    )
