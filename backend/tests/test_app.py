from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready() -> None:
    with TestClient(app) as scoped_client:
        response = scoped_client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] in {"ready", "initializing"}


def test_scan() -> None:
    response = client.post(
        "/api/v1/scan",
        json={"timeframe": "5m", "rules": [{"field": "rsi_14", "operator": ">", "value": 40}]},
    )
    assert response.status_code == 200
    assert "scan_id" in response.json()


def test_create_strategy_requires_headers() -> None:
    payload = {
        "user_id": "u1",
        "name": "Momentum",
        "rules": [{"field": "rsi_14", "operator": ">", "value": 50}],
    }
    response = client.post("/api/v1/strategies", json=payload)
    assert response.status_code in {400, 401}


def test_create_strategy_with_headers() -> None:
    payload = {
        "user_id": "u1",
        "name": "Momentum",
        "rules": [{"field": "rsi_14", "operator": ">", "value": 50}],
    }
    response = client.post(
        "/api/v1/strategies",
        json=payload,
        headers={"x-actor-id": "u1", "x-idempotency-key": "k-1"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Momentum"


def test_audit_events_recorded() -> None:
    payload = {
        "user_id": "u2",
        "name": "Reversal",
        "rules": [{"field": "ema_20", "operator": ">", "value": 100}],
    }
    create_response = client.post(
        "/api/v1/strategies",
        json=payload,
        headers={"x-actor-id": "u2", "x-idempotency-key": "k-2"},
    )
    assert create_response.status_code == 200

    audit_response = client.get("/api/v1/audit/events")
    assert audit_response.status_code == 200
    assert len(audit_response.json()) >= 1


def test_alert_filtering_by_user() -> None:
    payload_1 = {
        "user_id": "u-alert-1",
        "name": "Alert 1",
        "rule": {"field": "rsi_14", "operator": ">", "value": 55},
    }
    payload_2 = {
        "user_id": "u-alert-2",
        "name": "Alert 2",
        "rule": {"field": "rsi_14", "operator": ">", "value": 56},
    }

    headers = {"x-actor-id": "ops", "x-idempotency-key": "a-1"}
    response_1 = client.post("/api/v1/alerts", json=payload_1, headers=headers)
    assert response_1.status_code == 200
    headers["x-idempotency-key"] = "a-2"
    response_2 = client.post("/api/v1/alerts", json=payload_2, headers=headers)
    assert response_2.status_code == 200

    list_response = client.get("/api/v1/alerts", params={"user_id": "u-alert-1"})
    assert list_response.status_code == 200
    rows = list_response.json()
    assert len(rows) >= 1
    assert all(row["user_id"] == "u-alert-1" for row in rows)


def test_strategy_validation_rsi_range() -> None:
    payload = {
        "user_id": "u-bad",
        "name": "Bad RSI",
        "rules": [{"field": "rsi_14", "operator": ">", "value": 120}],
    }
    response = client.post(
        "/api/v1/strategies",
        json=payload,
        headers={"x-actor-id": "u-bad", "x-idempotency-key": "bad-1"},
    )
    assert response.status_code == 422


def test_idempotency_key_reuses_response() -> None:
    payload = {
        "user_id": "u-idem",
        "name": "Idem Strategy",
        "rules": [{"field": "rsi_14", "operator": ">", "value": 51}],
    }
    headers = {"x-actor-id": "u-idem", "x-idempotency-key": "idem-123"}
    first = client.post("/api/v1/strategies", json=payload, headers=headers)
    second = client.post("/api/v1/strategies", json=payload, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_audit_pagination_and_sort() -> None:
    for idx in range(3):
        payload = {
            "user_id": f"u-page-{idx}",
            "name": f"Strategy {idx}",
            "rules": [{"field": "rsi_14", "operator": ">", "value": 52}],
        }
        response = client.post(
            "/api/v1/strategies",
            json=payload,
            headers={"x-actor-id": f"u-page-{idx}", "x-idempotency-key": f"page-{idx}"},
        )
        assert response.status_code == 200

    page = client.get(
        "/api/v1/audit/events",
        params={"limit": 2, "offset": 0, "sort_by": "created_at", "sort_order": "desc"},
    )
    assert page.status_code == 200
    rows = page.json()
    assert len(rows) <= 2


def test_scan_results_persisted_lookup() -> None:
    scan_response = client.post(
        "/api/v1/scan",
        json={"timeframe": "5m", "rules": [{"field": "rsi_14", "operator": ">", "value": 20}]},
        headers={"x-actor-id": "scan-user"},
    )
    assert scan_response.status_code == 200
    scan_id = scan_response.json()["scan_id"]

    results_response = client.get(f"/api/v1/scan/{scan_id}/results")
    assert results_response.status_code == 200
    body = results_response.json()
    assert body["scan_id"] == scan_id
    assert body["status"] == "completed"
    assert isinstance(body["results"], list)


def test_scan_filters_by_underlying() -> None:
    response = client.post(
        "/api/v1/scan",
        json={
            "timeframe": "5m",
            "underlying": "NIFTY",
            "rules": [{"field": "rsi_14", "operator": ">", "value": 20}],
        },
    )
    assert response.status_code == 200
    rows = response.json()["results"]
    assert rows
    assert all(item["token"].startswith("NIFTY") for item in rows)


def test_scan_group_rules_with_or_operator() -> None:
    response = client.post(
        "/api/v1/scan",
        json={
            "timeframe": "5m",
            "groups": [
                {
                    "logical_operator": "OR",
                    "rules": [
                        {"field": "rsi_14", "operator": ">", "value": 80},
                        {"field": "ema_20", "operator": ">", "value": 90},
                    ],
                }
            ],
        },
    )
    assert response.status_code == 200
    assert "scan_id" in response.json()


def test_scan_supports_iv_and_oi_rules() -> None:
    response = client.post(
        "/api/v1/scan",
        json={
            "timeframe": "5m",
            "rules": [
                {"field": "iv", "operator": ">", "value": 10},
                {"field": "oi", "operator": ">", "value": 1000},
                {"field": "pcr", "operator": ">", "value": 0.5},
            ],
        },
    )
    assert response.status_code == 200
    assert "scan_id" in response.json()


def test_scan_can_queue_notifications_for_alert_user() -> None:
    pref = client.post(
        "/api/v1/notifications/preferences",
        json={
            "user_id": "u-scan-alert",
            "channel": "email",
            "destination": "scan-alert@example.com",
            "enabled": True,
        },
    )
    assert pref.status_code == 200

    response = client.post(
        "/api/v1/scan?alert_user_id=u-scan-alert",
        json={"timeframe": "5m", "rules": [{"field": "rsi_14", "operator": ">", "value": 20}]},
    )
    assert response.status_code == 200

    outbox = client.get("/api/v1/notifications/outbox", params={"user_id": "u-scan-alert"})
    assert outbox.status_code == 200
    assert len(outbox.json()) >= 1


def test_scan_supports_phase3_option_filter_fields() -> None:
    response = client.post(
        "/api/v1/scan",
        json={
            "timeframe": "5m",
            "rules": [
                {"field": "delta", "operator": ">", "value": 0.1},
                {"field": "gamma", "operator": ">", "value": 0.0001},
                {"field": "oi_change_pct", "operator": ">=", "value": 0},
                {"field": "volume", "operator": ">", "value": 100},
                {"field": "moneyness", "operator": "<=", "value": 5},
                {"field": "expiry_days", "operator": ">", "value": 1},
            ],
        },
    )
    assert response.status_code == 200
    assert "scan_id" in response.json()


def test_scan_option_filter_combinations() -> None:
    response = client.post(
        "/api/v1/scan",
        json={
            "timeframe": "5m",
            "groups": [
                {
                    "logical_operator": "AND",
                    "rules": [
                        {"field": "iv", "operator": ">", "value": 10},
                        {"field": "delta", "operator": ">", "value": 0.4},
                        {"field": "gamma", "operator": ">", "value": 0.0001},
                        {"field": "oi", "operator": ">", "value": 5000},
                        {"field": "oi_change_pct", "operator": ">", "value": 1},
                        {"field": "volume", "operator": ">", "value": 1000},
                        {"field": "moneyness", "operator": "<=", "value": 1},
                        {"field": "expiry_days", "operator": ">", "value": 5},
                    ],
                }
            ],
        },
    )
    assert response.status_code == 200
    rows = response.json()["results"]
    assert any(item["matched"] for item in rows)


def test_alerts_cursor_pagination() -> None:
    for idx in range(3):
        payload = {
            "user_id": "u-cursor",
            "name": f"Cursor Alert {idx}",
            "rule": {"field": "rsi_14", "operator": ">", "value": 55 + idx},
        }
        response = client.post(
            "/api/v1/alerts",
            json=payload,
            headers={"x-actor-id": "u-cursor", "x-idempotency-key": f"cursor-alert-{idx}"},
        )
        assert response.status_code == 200

    first_page = client.get("/api/v1/alerts/cursor", params={"user_id": "u-cursor", "limit": 2})
    assert first_page.status_code == 200
    body = first_page.json()
    assert len(body["items"]) <= 2
    assert body["next_cursor"] is not None

    second_page = client.get(
        "/api/v1/alerts/cursor",
        params={"user_id": "u-cursor", "limit": 2, "cursor": body["next_cursor"]},
    )
    assert second_page.status_code == 200


def test_screeners_crud() -> None:
    create_response = client.post(
        "/api/v1/screeners",
        json={
            "user_id": "u-screener",
            "name": "Momentum Builder",
            "timeframe": "5m",
            "groups": [
                {
                    "logical_operator": "AND",
                    "rules": [{"field": "rsi_14", "operator": ">", "value": 55}],
                }
            ],
        },
    )
    assert create_response.status_code == 200
    screener_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/screeners/{screener_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Momentum Builder"

    update_response = client.put(
        f"/api/v1/screeners/{screener_id}",
        json={"name": "Momentum Builder V2"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Momentum Builder V2"

    list_response = client.get("/api/v1/screeners", params={"user_id": "u-screener"})
    assert list_response.status_code == 200
    assert any(row["id"] == screener_id for row in list_response.json())

    delete_response = client.delete(f"/api/v1/screeners/{screener_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


def test_signals_endpoint_available() -> None:
    response = client.get("/api/v1/signals")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
