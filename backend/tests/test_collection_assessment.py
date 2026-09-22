"""IGR-05B collection serving contract and HTTP behavior."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.analytics.crop_median_baseline import CropMedianBaseline
from app.domain.assessment import RiskAssessmentCollectionResponse
from app.main import create_app
from app.runtime.artifact import DATASET_ID, ENGINE_VERSION
from app.runtime.context import AnalyticsRuntimeContext, get_runtime
from app.services.collection_assessment import (
    FacilityNotFoundError, InvalidWindowError, get_assessment_collection,
)
from test_ingestion_canonical import _make_synthetic_snapshot


def _collection_runtime() -> AnalyticsRuntimeContext:
    snapshot = _make_synthetic_snapshot()
    for table in snapshot.tables.values():
        for row in table.rows:
            for key, value in row.items():
                if isinstance(value, str):
                    row[key] = value.replace("2024-09-", "2025-04-").replace(
                        "2024-10-", "2025-05-"
                    )

    snapshot["facilities"].rows.append({
        **snapshot["facilities"].rows[0], "facility_id": "FAC-TEST-02",
    })
    snapshot["storage_zones"].rows.append({
        **snapshot["storage_zones"].rows[0],
        "zone_id": "ZONE-TEST-02", "facility_id": "FAC-TEST-02",
    })
    snapshot["sensor_readings"].rows.extend([
        {**row, "reading_id": row["reading_id"] + "-02", "zone_id": "ZONE-TEST-02"}
        for row in snapshot["sensor_readings"].rows
    ])
    templates = {
        name: deepcopy(snapshot[name].rows)
        for name in ("batches", "storage_sessions", "quality_checks", "shipments", "historical_quality_outcomes")
    }
    for name in templates:
        snapshot[name].rows.clear()

    def add(batch_id: str, crop: str, dispatch: str, zone: str = "ZONE-TEST-01") -> None:
        for name, rows in templates.items():
            for source in rows:
                row = dict(source)
                row["batch_id"] = batch_id
                if name == "batches":
                    row["crop_type"] = crop
                elif name == "storage_sessions":
                    row["storage_session_id"] = "SES-" + batch_id
                    row["zone_id"] = zone
                    row["dispatch_datetime"] = dispatch
                    row["planned_dispatch_datetime"] = dispatch
                elif name == "quality_checks":
                    row["check_id"] += "-" + batch_id
                elif name == "shipments":
                    row["shipment_id"] = "SHP-" + batch_id
                else:
                    row["loss_fraction_pct"] = "never read at request time"
                snapshot[name].rows.append(row)

    # Raw order starts with the lowest score; B and C tie at the top.
    add("A", "apples", "2025-05-01 12:00:00")
    add("C", "pears", "2025-05-02 12:00:00", "ZONE-TEST-02")
    add("B", "pears", "2025-05-01 13:00:00")
    add("D", "apples", "2025-05-03 00:00:00")
    add("TRAINING", "pears", "2025-05-01 12:00:00")
    return AnalyticsRuntimeContext(
        snapshot,
        CropMedianBaseline({"apples": 10.0, "pears": 90.0}, 50.0),
        frozenset({"TRAINING"}),
        frozenset({"A", "B", "C", "D"}),
    )


@pytest.fixture
def runtime() -> AnalyticsRuntimeContext:
    return _collection_runtime()


@pytest.fixture
def client(runtime):
    app = create_app()
    app.dependency_overrides[get_runtime] = lambda: runtime
    with TestClient(app) as test_client:
        yield test_client


def test_default_window_global_rank_and_contract(runtime):
    raw_dispatch = runtime.snapshot["storage_sessions"].rows[0]["dispatch_datetime"]
    result = get_assessment_collection(runtime)
    assert isinstance(result, RiskAssessmentCollectionResponse)
    assert result.window_start == datetime(2025, 5, 1, tzinfo=timezone.utc)
    assert result.window_end == datetime(2025, 5, 3, tzinfo=timezone.utc)
    assert result.facility_id is None
    assert result.engine_version == ENGINE_VERSION
    assert result.total_count == 3
    assert [(item.batch_id, item.risk.score) for item in result.items] == [
        ("B", 0.9), ("C", 0.9), ("A", 0.1),
    ]
    assert runtime.snapshot["storage_sessions"].rows[0]["dispatch_datetime"] == raw_dispatch
    for item in result.items:
        assert item.status == "assessed"
        assert item.risk.band is None
        assert item.deterioration_horizon is None
        assert item.factors == []
        assert item.recommendation is None
        assert item.reliability.level == "unavailable"
        assert item.reliability.confidence_score is None
        assert item.provenance.engine_tier == "deterministic_baseline"
        assert item.provenance.engine_version == ENGINE_VERSION
        assert item.provenance.source_dataset_id == DATASET_ID
        assert item.provenance.simulation is True


def test_explicit_half_open_window_facility_and_empty(runtime):
    start = datetime(2025, 5, 1, 12, tzinfo=timezone.utc)
    end = datetime(2025, 5, 2, 12, tzinfo=timezone.utc)
    result = get_assessment_collection(runtime, window_start=start, window_end=end)
    assert [item.batch_id for item in result.items] == ["B", "A"]
    # An offset boundary is converted to the same UTC clock as naive source rows.
    offset_start = datetime.fromisoformat("2025-05-01T14:00:00+02:00")
    assert [item.batch_id for item in get_assessment_collection(
        runtime, window_start=offset_start, window_end=end,
    ).items] == ["B", "A"]
    facility = get_assessment_collection(runtime, facility_id="FAC-TEST-02")
    assert facility.total_count == 1
    assert [item.batch_id for item in facility.items] == ["C"]
    zones = {row["zone_id"]: row["facility_id"] for row in runtime.snapshot["storage_zones"].rows}
    sessions = {row["batch_id"]: row for row in runtime.snapshot["storage_sessions"].rows}
    assert all(zones[sessions[item.batch_id]["zone_id"]] == "FAC-TEST-02" for item in facility.items)
    empty = get_assessment_collection(
        runtime,
        window_start=datetime(2025, 5, 10, tzinfo=timezone.utc),
        window_end=datetime(2025, 5, 11, tzinfo=timezone.utc),
        facility_id="FAC-TEST-02",
    )
    assert empty.total_count == 0
    assert empty.items == []


def test_rank_before_slice_offset_and_page_bounds(runtime):
    assert [item.batch_id for item in get_assessment_collection(runtime, limit=1).items] == ["B"]
    assert [item.batch_id for item in get_assessment_collection(runtime, limit=1, offset=1).items] == ["C"]
    beyond = get_assessment_collection(runtime, offset=100)
    assert beyond.items == []
    assert beyond.total_count == 3

    # Add 22 low-risk rows; default page is 20 even though all 25 are scored.
    source_batch = runtime.snapshot["batches"].rows[0]
    source_session = runtime.snapshot["storage_sessions"].rows[0]
    source_checks = [r for r in runtime.snapshot["quality_checks"].rows if r["batch_id"] == "A"]
    source_shipment = runtime.snapshot["shipments"].rows[0]
    held_out = set(runtime.held_out_ids)
    for index in range(22):
        batch_id = f"EXTRA-{index:02d}"
        runtime.snapshot["batches"].rows.append({**source_batch, "batch_id": batch_id})
        runtime.snapshot["storage_sessions"].rows.append({
            **source_session, "batch_id": batch_id, "storage_session_id": "SES-" + batch_id,
        })
        runtime.snapshot["quality_checks"].rows.extend([
            {**row, "batch_id": batch_id, "check_id": row["check_id"] + batch_id}
            for row in source_checks
        ])
        runtime.snapshot["shipments"].rows.append({
            **source_shipment, "batch_id": batch_id, "shipment_id": "SHP-" + batch_id,
        })
        held_out.add(batch_id)
    runtime = AnalyticsRuntimeContext(runtime.snapshot, runtime.baseline, runtime.training_ids, frozenset(held_out))
    default = get_assessment_collection(runtime)
    assert default.total_count == 25
    assert len(default.items) == 20
    assert len(get_assessment_collection(runtime, limit=50).items) == 25
    assert [item.batch_id for item in get_assessment_collection(runtime, offset=20).items] == [
        f"EXTRA-{index:02d}" for index in range(17, 22)
    ]


def test_service_rejects_invalid_window_and_unknown_facility(runtime):
    start = datetime(2025, 5, 1, tzinfo=timezone.utc)
    with pytest.raises(InvalidWindowError):
        get_assessment_collection(runtime, window_start=start)
    with pytest.raises(InvalidWindowError):
        get_assessment_collection(runtime, window_end=start)
    with pytest.raises(InvalidWindowError):
        get_assessment_collection(runtime, window_start=start, window_end=start)
    with pytest.raises(InvalidWindowError):
        get_assessment_collection(runtime, window_start=start, window_end=datetime(2025, 4, 30))
    with pytest.raises(FacilityNotFoundError):
        get_assessment_collection(runtime, facility_id="UNKNOWN")


def test_http_collection_contract_and_single_batch_preservation(client):
    response = client.get("/api/v1/assessments")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert set(payload) == {
        "items", "total_count", "window_start", "window_end", "facility_id", "engine_version",
    }
    assert payload["window_start"] == "2025-05-01T00:00:00Z"
    assert payload["window_end"] == "2025-05-03T00:00:00Z"
    assert payload["total_count"] == 3
    assert [item["batch_id"] for item in payload["items"]] == ["B", "C", "A"]
    assert client.get("/api/v1/assessments/B").status_code == 200
    assert client.get("/api/v1/assessments/TRAINING").status_code == 409
    assert client.get("/api/v1/assessments/UNKNOWN").status_code == 404


def test_http_filters_validation_and_unavailable(client):
    assert [item["batch_id"] for item in client.get(
        "/api/v1/assessments", params={"facility_id": "FAC-TEST-02"},
    ).json()["items"]] == ["C"]
    empty = client.get("/api/v1/assessments", params={
        "facility_id": "FAC-TEST-02",
        "window_start": "2025-05-10T00:00:00Z",
        "window_end": "2025-05-11T00:00:00Z",
    })
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["total_count"] == 0
    for params in (
        {"window_start": "2025-05-01T00:00:00Z"},
        {"window_end": "2025-05-03T00:00:00Z"},
        {"window_start": "2025-05-03T00:00:00Z", "window_end": "2025-05-01T00:00:00Z"},
    ):
        assert client.get("/api/v1/assessments", params=params).status_code == 400
    assert client.get("/api/v1/assessments", params={"facility_id": "UNKNOWN"}).status_code == 404
    for params in ({"limit": 0}, {"limit": 51}, {"offset": -1}):
        assert client.get("/api/v1/assessments", params=params).status_code == 422
    assert client.get("/api/v1/assessments", params={"limit": 50}).status_code == 200
    assert [item["batch_id"] for item in client.get(
        "/api/v1/assessments", params={"limit": 1, "offset": 1},
    ).json()["items"]] == ["C"]
    with TestClient(create_app()) as unavailable_client:
        assert unavailable_client.get("/api/v1/assessments").status_code == 503


def test_mapping_failure_fails_entire_page(client, runtime):
    # C is ranked second, beyond limit=1, but must still map successfully.
    next(row for row in runtime.snapshot["batches"].rows if row["batch_id"] == "C")[
        "harvest_weight_kg"
    ] = "malformed"
    response = client.get("/api/v1/assessments", params={"limit": 1})
    assert response.status_code == 500
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"detail": "Assessment collection could not be completed"}
