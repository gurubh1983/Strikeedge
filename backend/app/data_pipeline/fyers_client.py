from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from typing import Any

import httpx
try:  # pragma: no cover - optional runtime dependency usage
    from fyers_apiv3 import fyersModel as _fyers_model  # type: ignore
except Exception:  # pragma: no cover
    _fyers_model = None


INSTRUMENT_MASTER_URL = "https://public.fyers.in/sym_details/NSE_FO.csv"


@dataclass(slots=True)
class FyersCredentials:
    app_id: str
    secret_key: str
    redirect_uri: str
    totp_secret: str


class FyersClient:
    """
    Lightweight Fyers API v3 integration utilities used by instrument sync.
    Authentication/session flow is implemented in app.data_pipeline.fyers_auth.
    """

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def fetch_scrip_master(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(INSTRUMENT_MASTER_URL)
            response.raise_for_status()
        text = response.text
        if not text.strip():
            return []
        reader = csv.DictReader(StringIO(text))
        return [dict(row) for row in reader]

    @staticmethod
    def _value(item: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = item.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    @staticmethod
    def filter_nfo_options(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in records:
            exchange = FyersClient._value(item, "exch_seg", "exchange", "exchangeSegment").upper()
            instrument = FyersClient._value(item, "instrumenttype", "instrument_type", "instrumentType").upper()
            symbol = FyersClient._value(item, "symbol", "symbol_ticker", "trading_symbol").upper()
            if exchange and exchange not in {"NFO", "NSE_FO"}:
                continue
            if instrument and not instrument.startswith("OPT"):
                continue
            if not (symbol.endswith("CE") or symbol.endswith("PE")):
                continue
            out.append(item)
        return out

    @staticmethod
    def filter_by_expiry(records: list[dict[str, Any]], expiry_iso: str) -> list[dict[str, Any]]:
        target = expiry_iso.strip()
        out: list[dict[str, Any]] = []
        for item in records:
            expiry = FyersClient._value(item, "expiry", "expiryDate", "expiry_date")
            if expiry == target:
                out.append(item)
        return out

    @staticmethod
    def filter_by_strike_range(records: list[dict[str, Any]], min_strike: float, max_strike: float) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in records:
            strike_raw = FyersClient._value(item, "strike", "strike_price", "strikePrice")
            if not strike_raw:
                continue
            try:
                strike_value = float(strike_raw) / 100.0 if float(strike_raw) > 100000 else float(strike_raw)
            except (TypeError, ValueError):
                continue
            if min_strike <= strike_value <= max_strike:
                out.append(item)
        return out

    @staticmethod
    def normalize_record(item: dict[str, Any]) -> dict[str, Any]:
        symbol = FyersClient._value(item, "symbol", "symbol_ticker", "trading_symbol")
        option_type = "CE" if symbol.upper().endswith("CE") else ("PE" if symbol.upper().endswith("PE") else None)
        strike_raw = FyersClient._value(item, "strike", "strike_price", "strikePrice")
        strike_price = None
        if strike_raw:
            try:
                strike_price = float(strike_raw) / 100.0 if float(strike_raw) > 100000 else float(strike_raw)
            except (TypeError, ValueError):
                strike_price = None
        expiry = FyersClient._value(item, "expiry", "expiryDate", "expiry_date") or None
        return {
            "token": FyersClient._value(item, "token", "symbol_token", "symbolToken"),
            "symbol": symbol,
            "name": FyersClient._value(item, "name", "underlying", "underlying_name"),
            "exchange": FyersClient._value(item, "exch_seg", "exchange", "exchangeSegment") or "NFO",
            "instrument_type": FyersClient._value(item, "instrumenttype", "instrument_type", "instrumentType"),
            "underlying": FyersClient._value(item, "name", "underlying", "underlying_name"),
            "option_type": option_type,
            "strike_price": strike_price,
            "expiry": expiry,
            "lot_size": int(FyersClient._value(item, "lotsize", "lot_size", "lotSize") or 1),
            "updated_at": datetime.utcnow(),
        }

    @staticmethod
    def build_options_chain(records: list[dict[str, Any]], *, underlying: str, expiry: str) -> list[dict[str, Any]]:
        filtered = FyersClient.filter_nfo_options(records)
        filtered = FyersClient.filter_by_expiry(filtered, expiry)
        grouped: dict[float, dict[str, Any]] = {}
        target_underlying = underlying.upper()
        for item in filtered:
            name = FyersClient._value(item, "name", "underlying", "underlying_name").upper()
            symbol = FyersClient._value(item, "symbol", "symbol_ticker", "trading_symbol").upper()
            if target_underlying not in name and target_underlying not in symbol:
                continue
            strike_raw = FyersClient._value(item, "strike", "strike_price", "strikePrice")
            if not strike_raw:
                continue
            try:
                strike_value = float(strike_raw) / 100.0 if float(strike_raw) > 100000 else float(strike_raw)
            except (TypeError, ValueError):
                continue
            row = grouped.setdefault(
                strike_value,
                {
                    "strike_price": strike_value,
                    "call_token": None,
                    "call_symbol": None,
                    "call_oi": None,
                    "call_iv": None,
                    "put_token": None,
                    "put_symbol": None,
                    "put_oi": None,
                    "put_iv": None,
                    "put_call_ratio": None,
                    "total_oi_change": None,
                    "lot_size": int(FyersClient._value(item, "lotsize", "lot_size", "lotSize") or 1),
                },
            )
            token = FyersClient._value(item, "token", "symbol_token", "symbolToken")
            oi_value = FyersClient._parse_int(item.get("oi") or item.get("open_interest") or item.get("openinterest"))
            iv_value = FyersClient._parse_float(item.get("iv") or item.get("implied_volatility"))
            if symbol.endswith("CE"):
                row["call_token"] = token or row["call_token"]
                row["call_symbol"] = FyersClient._value(item, "symbol", "symbol_ticker", "trading_symbol") or row["call_symbol"]
                row["call_oi"] = oi_value if oi_value is not None else row["call_oi"]
                row["call_iv"] = iv_value if iv_value is not None else row["call_iv"]
            elif symbol.endswith("PE"):
                row["put_token"] = token or row["put_token"]
                row["put_symbol"] = FyersClient._value(item, "symbol", "symbol_ticker", "trading_symbol") or row["put_symbol"]
                row["put_oi"] = oi_value if oi_value is not None else row["put_oi"]
                row["put_iv"] = iv_value if iv_value is not None else row["put_iv"]
        for row in grouped.values():
            call_oi = row.get("call_oi")
            put_oi = row.get("put_oi")
            if call_oi and call_oi > 0 and put_oi is not None:
                row["put_call_ratio"] = round(float(put_oi) / float(call_oi), 4)
        out = list(grouped.values())
        out.sort(key=lambda x: float(x["strike_price"]))
        return out

    @staticmethod
    def _parse_float(value: Any) -> float | None:
        try:
            if value in (None, ""):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_int(value: Any) -> int | None:
        try:
            if value in (None, ""):
                return None
            return int(float(value))
        except (TypeError, ValueError):
            return None
