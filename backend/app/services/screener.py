from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.logging import get_logger, log_event
from app.core.metrics import metrics_registry
from app.domain.indicators import ema, rsi
from app.screener.scanner import ConditionGroup, IndicatorCondition, evaluate_group
from app.schemas import ScanRequest, ScanResultOut
from app.services.market_data import market_data_service
from app.services.scan_store import scan_store_service

logger = get_logger("strikeedge.screener")


@dataclass(slots=True)
class Candle:
    ts: datetime
    close: float


class ScreenerService:
    @staticmethod
    def _eval_rule(value: float, operator: str, target: float) -> bool:
        if operator == ">":
            return value > target
        if operator == "<":
            return value < target
        if operator == ">=":
            return value >= target
        if operator == "<=":
            return value <= target
        return value == target

    def _sample_indicator_rows(self) -> list[dict]:
        candles = [Candle(datetime.now(timezone.utc) - timedelta(minutes=i), 100 + i) for i in range(40)]
        closes = [c.close for c in candles]
        return [
            {
                "token": "NIFTY_24000_CE",
                "rsi_14": rsi(closes),
                "ema_20": ema(closes, 20),
                "macd": 0.3,
                "macd_signal": 0.2,
                "iv": 16.2,
                "oi": 12000,
                "pcr": 1.08,
                "delta": 0.54,
                "gamma": 0.00042,
                "oi_change_pct": 8.4,
                "volume": 1800,
                "moneyness": 0.0,
                "expiry_days": 20.0,
            },
            {
                "token": "NIFTY_24000_PE",
                "rsi_14": 42.0,
                "ema_20": 98.0,
                "macd": -0.2,
                "macd_signal": -0.1,
                "iv": 18.0,
                "oi": 14000,
                "pcr": 1.08,
                "delta": -0.46,
                "gamma": 0.00039,
                "oi_change_pct": 12.1,
                "volume": 2200,
                "moneyness": 0.0,
                "expiry_days": 20.0,
            },
        ]

    def run_scan(self, payload: ScanRequest) -> tuple[str, list[ScanResultOut], list[dict]]:
        rows, previous_rows = market_data_service.latest_and_previous_indicator_rows(timeframe=payload.timeframe)
        if not rows:
            rows = self._sample_indicator_rows()
            previous_rows = {}
        if payload.underlying:
            prefix = payload.underlying.upper()
            rows = [row for row in rows if str(row.get("token", "")).startswith(prefix)]
        if payload.limit > 0:
            rows = rows[: payload.limit]
        rows = [self._enrich_option_row(row) for row in rows]
        out: list[ScanResultOut] = []
        deltas: list[dict] = []
        for row in rows:
            token = str(row.get("token", ""))
            previous = previous_rows.get(token)
            matched = self._evaluate_payload_rules(row=row, previous=previous, payload=payload)
            out.append(
                ScanResultOut(
                    token=row["token"],
                    matched=matched,
                    reason="all rules satisfied" if matched else "rule mismatch",
                )
            )
            deltas.append({"token": row["token"], "matched": matched, "reason": out[-1].reason})
        scan_id = scan_store_service.save_scan(
            timeframe=payload.timeframe,
            rules=[rule.model_dump() for rule in payload.rules],
            results=out,
        )
        matched_count = sum(1 for item in out if item.matched)
        log_event(
            logger,
            "scan_executed",
            scan_id=scan_id,
            timeframe=payload.timeframe,
            rule_count=len(payload.rules),
            total=len(out),
            matched=matched_count,
        )
        metrics_registry.incr("service_scan_execute_total")
        metrics_registry.incr("service_scan_match_total", matched_count)
        return scan_id, out, deltas

    def _evaluate_payload_rules(self, *, row: dict, previous: dict | None, payload: ScanRequest) -> bool:
        group_results: list[bool] = []
        for group in payload.groups:
            parsed_group = ConditionGroup(
                logical_operator=group.logical_operator,
                conditions=[
                    IndicatorCondition(field=rule.field, operator=rule.operator, value=rule.value)
                    for rule in group.rules
                ],
            )
            group_results.append(evaluate_group(row, previous, parsed_group))
        flat_results: list[bool] = []
        for rule in payload.rules:
            value = row.get(rule.field)
            prev_value = previous.get(rule.field) if previous else None
            if rule.operator == "crosses_above":
                flat_results.append(prev_value is not None and value is not None and float(prev_value) <= rule.value and float(value) > rule.value)
            elif rule.operator == "crosses_below":
                flat_results.append(prev_value is not None and value is not None and float(prev_value) >= rule.value and float(value) < rule.value)
            else:
                flat_results.append(value is not None and self._eval_rule(float(value), rule.operator, rule.value))

        checks = group_results + flat_results
        return all(checks) if checks else True

    @staticmethod
    def _enrich_option_row(row: dict) -> dict:
        out = dict(row)
        token = str(out.get("token", "")).upper()
        oi = float(out.get("oi") or 0.0)
        out.setdefault("volume", max(oi / 8.0, 0.0))
        out.setdefault("oi_change_pct", 0.0)
        out.setdefault("expiry_days", 20.0)
        out.setdefault("moneyness", 0.0)
        if "delta" not in out:
            out["delta"] = -0.45 if token.endswith("_PE") or token.endswith("PE") else 0.55
        out.setdefault("gamma", 0.0004)
        return out


screener_service = ScreenerService()
