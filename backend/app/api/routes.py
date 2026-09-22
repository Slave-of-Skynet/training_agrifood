"""Versioned foundation endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from app.domain.assessment import HealthResponse, RiskAssessment, RiskAssessmentCollectionResponse
from app.services.demo_assessment import build_demo_assessment
from app.ingestion.canonical_mapper import build_batch_assessment_input
from app.runtime.artifact import DATASET_ID, ENGINE_VERSION, NOTICE
from app.runtime.context import AnalyticsRuntimeContext, get_runtime
from app.services.baseline_assessment import build_baseline_assessment
from app.services.collection_assessment import (
    FacilityNotFoundError, InvalidWindowError, get_assessment_collection,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="smart-harvest",
        analytics=request.app.state.analytics_runtime.analytics,
    )


@router.get("/demo/assessment", response_model=RiskAssessment)
def demo_assessment() -> RiskAssessment:
    """Return a synthetic contract fixture; this is not challenge data."""

    return build_demo_assessment()


@router.get("/assessments", response_model=RiskAssessmentCollectionResponse)
def assessment_collection(
    response: Response,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
    facility_id: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    runtime: AnalyticsRuntimeContext = Depends(get_runtime),
) -> RiskAssessmentCollectionResponse:
    headers = {"Cache-Control": "no-store"}
    response.headers.update(headers)
    try:
        return get_assessment_collection(
            runtime,
            window_start=window_start,
            window_end=window_end,
            facility_id=facility_id,
            limit=limit,
            offset=offset,
        )
    except InvalidWindowError as error:
        raise HTTPException(400, str(error), headers=headers) from None
    except FacilityNotFoundError:
        raise HTTPException(404, "Facility not found", headers=headers) from None
    except Exception:
        logger.exception("Dataset-backed collection assessment failed")
        raise HTTPException(500, "Assessment collection could not be completed", headers=headers) from None


@router.get("/assessments/{batch_id}", response_model=RiskAssessment)
def assessment(
    batch_id: str,
    response: Response,
    runtime: AnalyticsRuntimeContext = Depends(get_runtime),
) -> RiskAssessment:
    headers = {"Cache-Control": "no-store"}
    response.headers.update(headers)
    if batch_id in runtime.training_ids:
        raise HTTPException(409, "Batch is not eligible for this assessment release", headers=headers)
    if batch_id not in runtime.held_out_ids:
        raise HTTPException(404, "Batch not found", headers=headers)
    try:
        batch_input = build_batch_assessment_input(runtime.snapshot, batch_id)
        return build_baseline_assessment(
            runtime.baseline, batch_input,
            engine_version=ENGINE_VERSION,
            generated_at=datetime.now(timezone.utc),
            source_dataset_id=DATASET_ID,
            simulation=True,
            notice=NOTICE,
        )
    except Exception:
        logger.exception("Dataset-backed assessment failed")
        raise HTTPException(500, "Assessment could not be completed", headers=headers) from None
