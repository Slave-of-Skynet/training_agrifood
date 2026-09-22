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
    FacilityNotFoundError, InvalidWindowError, SOURCE_TIMEZONE, get_assessment_collection,
)
from test_ingestion_canonical import _make_synthetic_snapshot


def _collection_runtime() -> AnalyticsRuntimeContext:
    snapshot = _make_synthetic_snapshot()
    for table in snapshot.tables.values():
        for row in table.rows:
            for key, value in row.items():
                if isinstance(value, str):
                    row[key] = value.replace("2024-09-", "2025-10-").replace(
                        "2024-10-", "2025-11-"
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
    add("A", "apples", "2025-11-29 12:00:00")
    add("C", "pears", "2025-11-30 12:00:00", "ZONE-TEST-02")
    add("B", "pears", "2025-11-29 13:00:00")
    add("D", "apples", "2025-12-01 00:00:00")
    add("TRAINING", "pears", "2025-11-29 12:00:00")
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
    assert result.window_start == datetime(2025, 11, 29, tzinfo=SOURCE_TIMEZONE)
    assert result.window_end == datetime(2025, 12, 1, tzinfo=SOURCE_TIMEZONE)
    assert result.facility_id is None
    assert result.engine_version == ENGINE_VERSION
    assert result.total_count == 3
    assert [(item.batch_id, item.risk.score) for item in result.items] == [
        ("B", 0.9), ("C", 0.9), ("A", 0.1),
    ]
    # D is exactly at the exclusive Dec 1 boundary; TRAINING is inside the window.
    assert result.items
    assert {item.batch_id for item in result.items}.isdisjoint({"D", "TRAINING"})
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
    start = datetime(2025, 11, 29, 12, tzinfo=SOURCE_TIMEZONE)
    end = datetime(2025, 11, 30, 12, tzinfo=SOURCE_TIMEZONE)
    result = get_assessment_collection(runtime, window_start=start, window_end=end)
    assert [item.batch_id for item in result.items] == ["B", "A"]
    # An offset boundary is converted to the same source clock as naive source rows.
    offset_start = datetime.fromisoformat("2025-11-29T11:00:00+02:00")
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
        window_start=datetime(2025, 12, 10, tzinfo=SOURCE_TIMEZONE),
        window_end=datetime(2025, 12, 11, tzinfo=SOURCE_TIMEZONE),
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
    start = datetime(2025, 11, 29, tzinfo=timezone.utc)
    with pytest.raises(InvalidWindowError):
        get_assessment_collection(runtime, window_start=start)
    with pytest.raises(InvalidWindowError):
        get_assessment_collection(runtime, window_end=start)
    with pytest.raises(InvalidWindowError):
        get_assessment_collection(runtime, window_start=start, window_end=start)
    with pytest.raises(InvalidWindowError):
        get_assessment_collection(runtime, window_start=start, window_end=datetime(2025, 11, 28))
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
    assert payload["window_start"] == "2025-11-29T00:00:00+03:00"
    assert payload["window_end"] == "2025-12-01T00:00:00+03:00"
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
        "window_start": "2025-12-10T00:00:00Z",
        "window_end": "2025-12-11T00:00:00Z",
    })
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["total_count"] == 0
    for params in (
        {"window_start": "2025-11-29T00:00:00Z"},
        {"window_end": "2025-12-01T00:00:00Z"},
        {"window_start": "2025-12-01T00:00:00Z", "window_end": "2025-11-29T00:00:00Z"},
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


def test_source_time_semantics_distinguishing_old_utc_clock(runtime):
    """Verify source-local timestamp semantics and equivalent aware API boundaries (TEMP-R1).

    Under the old _utc_clock implementation:
    - Naive source row '2025-11-29 00:30:00' was incorrectly assigned UTC (2025-11-29T00:30:00Z).
    - Source-local aware window [2025-11-29T00:00:00+03:00, 2025-11-29T01:00:00+03:00) was
      converted to UTC [2025-11-28T21:00:00Z, 2025-11-28T22:00:00Z), completely missing the row.
    - Thus, source-local aware and naive queries gave conflicting results, and equivalent
      physical instants did not match naive queries.
    """
    # 9.2: Create synthetic held-out batches at specific source-local timestamps
    source_batch = runtime.snapshot["batches"].rows[0]
    source_session = runtime.snapshot["storage_sessions"].rows[0]
    source_checks = [r for r in runtime.snapshot["quality_checks"].rows if r["batch_id"] == "A"]
    source_shipment = runtime.snapshot["shipments"].rows[0]

    def add_probe(batch_id: str, dispatch_str: str) -> None:
        runtime.snapshot["batches"].rows.append({**source_batch, "batch_id": batch_id, "crop_type": "apples"})
        runtime.snapshot["storage_sessions"].rows.append({
            **source_session, "batch_id": batch_id, "storage_session_id": f"SES-{batch_id}",
            "dispatch_datetime": dispatch_str, "planned_dispatch_datetime": dispatch_str,
        })
        runtime.snapshot["quality_checks"].rows.extend([
            {**r, "batch_id": batch_id, "check_id": f"{r['check_id']}-{batch_id}"}
            for r in source_checks
        ])
        runtime.snapshot["shipments"].rows.append({
            **source_shipment, "batch_id": batch_id, "shipment_id": f"SHP-{batch_id}",
        })

    add_probe("BATCH-INSIDE-0030", "2025-11-29 00:30:00")
    add_probe("BATCH-EXCLUDED-0100", "2025-11-29 01:00:00")
    new_held_out = frozenset(runtime.held_out_ids | {"BATCH-INSIDE-0030", "BATCH-EXCLUDED-0100"})
    probe_runtime = AnalyticsRuntimeContext(runtime.snapshot, runtime.baseline, runtime.training_ids, new_held_out)

    # 9.1: Default response timezone
    default_result = get_assessment_collection(probe_runtime)
    assert default_result.window_start == datetime(2025, 11, 29, 0, 0, 0, tzinfo=SOURCE_TIMEZONE)
    assert default_result.window_end == datetime(2025, 12, 1, 0, 0, 0, tzinfo=SOURCE_TIMEZONE)
    assert str(default_result.window_start.tzinfo) == "UTC+03:00"

    # 9.3: Equivalent aware boundaries describe the exact same physical interval
    # Source-local aware (+03:00)
    w_source_aware = get_assessment_collection(
        probe_runtime,
        window_start=datetime.fromisoformat("2025-11-29T00:00:00+03:00"),
        window_end=datetime.fromisoformat("2025-11-29T01:00:00+03:00"),
    )
    # UTC equivalent (instant is identical: 2025-11-28 21:00:00Z to 22:00:00Z)
    w_utc = get_assessment_collection(
        probe_runtime,
        window_start=datetime.fromisoformat("2025-11-28T21:00:00Z"),
        window_end=datetime.fromisoformat("2025-11-28T22:00:00Z"),
    )
    # +02:00 equivalent (instant is identical: 2025-11-28 23:00:00+02:00 to 2025-11-29 00:00:00+02:00)
    w_plus2 = get_assessment_collection(
        probe_runtime,
        window_start=datetime.fromisoformat("2025-11-28T23:00:00+02:00"),
        window_end=datetime.fromisoformat("2025-11-29T00:00:00+02:00"),
    )

    # 9.4: Naive explicit boundaries interpreted as source-local UTC+03
    w_naive = get_assessment_collection(
        probe_runtime,
        window_start=datetime.fromisoformat("2025-11-29T00:00:00"),
        window_end=datetime.fromisoformat("2025-11-29T01:00:00"),
    )

    # 9.5: Half-open boundary: BATCH-INSIDE-0030 is included; BATCH-EXCLUDED-0100 is excluded
    expected_ids = ["BATCH-INSIDE-0030"]
    for collection in (w_source_aware, w_utc, w_plus2, w_naive):
        assert [item.batch_id for item in collection.items] == expected_ids
        assert collection.total_count == 1
        assert collection.window_start == datetime(2025, 11, 29, 0, 0, tzinfo=SOURCE_TIMEZONE)
        assert collection.window_end == datetime(2025, 11, 29, 1, 0, tzinfo=SOURCE_TIMEZONE)

    # HTTP endpoint serialization: test all representations via TestClient
    app = create_app()
    app.dependency_overrides[get_runtime] = lambda: probe_runtime
    with TestClient(app) as test_client:
        # Default window response contains +03:00
        resp_def = test_client.get("/api/v1/assessments")
        assert resp_def.status_code == 200
        assert resp_def.json()["window_start"] == "2025-11-29T00:00:00+03:00"
        assert resp_def.json()["window_end"] == "2025-12-01T00:00:00+03:00"

        # Naive HTTP query
        resp_naive = test_client.get(
            "/api/v1/assessments",
            params={"window_start": "2025-11-29T00:00:00", "window_end": "2025-11-29T01:00:00"},
        )
        assert resp_naive.status_code == 200
        data_naive = resp_naive.json()
        assert [item["batch_id"] for item in data_naive["items"]] == expected_ids
        assert data_naive["window_start"] == "2025-11-29T00:00:00+03:00"
        assert data_naive["window_end"] == "2025-11-29T01:00:00+03:00"

        # UTC equivalent HTTP query
        resp_utc = test_client.get(
            "/api/v1/assessments",
            params={"window_start": "2025-11-28T21:00:00Z", "window_end": "2025-11-28T22:00:00Z"},
        )
        assert resp_utc.status_code == 200
        data_utc = resp_utc.json()
        assert [item["batch_id"] for item in data_utc["items"]] == expected_ids
        assert data_utc["window_start"] == "2025-11-29T00:00:00+03:00"
        assert data_utc["window_end"] == "2025-11-29T01:00:00+03:00"

        # +02:00 equivalent HTTP query
        resp_plus2 = test_client.get(
            "/api/v1/assessments",
            params={"window_start": "2025-11-28T23:00:00+02:00", "window_end": "2025-11-29T00:00:00+02:00"},
        )
        assert resp_plus2.status_code == 200
        data_plus2 = resp_plus2.json()
        assert [item["batch_id"] for item in data_plus2["items"]] == expected_ids
        assert data_plus2["window_start"] == "2025-11-29T00:00:00+03:00"
        assert data_plus2["window_end"] == "2025-11-29T01:00:00+03:00"

        # Source-local aware (+03:00) HTTP query
        resp_aware = test_client.get(
            "/api/v1/assessments",
            params={"window_start": "2025-11-29T00:00:00+03:00", "window_end": "2025-11-29T01:00:00+03:00"},
        )
        assert resp_aware.status_code == 200
        data_aware = resp_aware.json()
        assert [item["batch_id"] for item in data_aware["items"]] == expected_ids
        assert data_aware["window_start"] == "2025-11-29T00:00:00+03:00"
        assert data_aware["window_end"] == "2025-11-29T01:00:00+03:00"

    # 9.6: Raw source immutability
    session_rows = {r["batch_id"]: r["dispatch_datetime"] for r in probe_runtime.snapshot["storage_sessions"].rows}
    assert session_rows["BATCH-INSIDE-0030"] == "2025-11-29 00:30:00"
    assert session_rows["BATCH-EXCLUDED-0100"] == "2025-11-29 01:00:00"
