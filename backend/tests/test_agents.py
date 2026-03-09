"""Phase 5 agent orchestration and workflow tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_create_and_run_scan_job() -> None:
    client = TestClient(app)
    client.get("/health")
    create = client.post(
        "/api/v1/agents/jobs",
        json={
            "job_type": "SCAN",
            "request_payload": {
                "workflow": "SCAN",
                "underlying": "NIFTY",
                "timeframe": "5m",
                "rules": [{"field": "rsi_14", "operator": ">", "value": 20}],
            },
        },
        headers={"x-actor-id": "user-1"},
    )
    assert create.status_code == 200
    job_id = create.json()["id"]
    assert create.json()["status"] == "pending"

    get_before = client.get(f"/api/v1/agents/jobs/{job_id}")
    assert get_before.status_code == 200, f"Job should exist after create: {get_before.text}"
    assert get_before.json()["status"] == "pending"

    run = client.post(f"/api/v1/agents/jobs/{job_id}/run")
    assert run.status_code == 200, f"Run should succeed: {run.text}"
    body = run.json()
    assert body["status"] in {"completed", "failed"}

    get_job = client.get(f"/api/v1/agents/jobs/{job_id}")
    assert get_job.status_code == 200
    assert get_job.json()["job_type"] == "SCAN"


def test_backtest_workflow() -> None:
    client = TestClient(app)
    create = client.post(
        "/api/v1/agents/jobs",
        json={
            "job_type": "BACKTEST",
            "request_payload": {
                "workflow": "BACKTEST",
                "underlying": "NIFTY",
                "timeframe": "5m",
                "rules": [{"field": "rsi_14", "operator": ">", "value": 30}],
            },
        },
        headers={"x-actor-id": "user-2"},
    )
    assert create.status_code == 200
    job_id = create.json()["id"]

    run = client.post(f"/api/v1/agents/jobs/{job_id}/run")
    assert run.status_code == 200
    body = run.json()
    assert "output" in body


def test_analyze_workflow() -> None:
    client = TestClient(app)
    create = client.post(
        "/api/v1/agents/jobs",
        json={
            "job_type": "ANALYZE",
            "request_payload": {
                "workflow": "ANALYZE",
                "underlying": "NIFTY",
                "spot": 24000,
                "expiry": "2026-04-24",
            },
        },
        headers={"x-actor-id": "user-3"},
    )
    assert create.status_code == 200
    job_id = create.json()["id"]

    run = client.post(f"/api/v1/agents/jobs/{job_id}/run")
    assert run.status_code == 200


def test_agent_job_not_found() -> None:
    client = TestClient(app)
    run = client.post("/api/v1/agents/jobs/nonexistent-id/run")
    assert run.status_code == 404

    get_job = client.get("/api/v1/agents/jobs/nonexistent-id")
    assert get_job.status_code == 404


def test_performance_scan_job_completes_under_30s() -> None:
    """Performance benchmark: SCAN workflow completes within 30 seconds."""
    import time
    client = TestClient(app)
    create = client.post(
        "/api/v1/agents/jobs",
        json={
            "job_type": "SCAN",
            "request_payload": {
                "workflow": "SCAN",
                "underlying": "NIFTY",
                "timeframe": "5m",
                "limit": 100,
            },
        },
        headers={"x-actor-id": "bench-user"},
    )
    assert create.status_code == 200
    job_id = create.json()["id"]
    start = time.perf_counter()
    run = client.post(f"/api/v1/agents/jobs/{job_id}/run")
    elapsed = time.perf_counter() - start
    assert run.status_code == 200
    assert elapsed < 30.0, f"SCAN workflow took {elapsed:.1f}s (max 30s)"
