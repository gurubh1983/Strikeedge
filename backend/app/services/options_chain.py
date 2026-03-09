from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.data_pipeline.fyers_client import FyersClient
from app.repositories.options_chain import OptionsChainRepository


def _fyers_symbol(sym: str) -> str:
    """Ensure symbol has NSE: prefix for Fyers API."""
    s = (sym or "").strip()
    if not s:
        return ""
    if ":" in s:
        return s
    return f"NSE:{s}"


def _enrich_chain_with_ltp(rows: list[dict]) -> None:
    """Enrich chain rows with LTP from Fyers quotes. Mutates rows in place."""
    symbols = []
    for r in rows:
        for col in ("call_symbol", "put_symbol"):
            s = r.get(col)
            if s:
                symbols.append(_fyers_symbol(s))
    if not symbols:
        return
    try:
        from app.services.fyers_data import get_quotes
        quotes = get_quotes(symbols[:50])
        for r in rows:
            cs = r.get("call_symbol")
            ps = r.get("put_symbol")
            if cs:
                k = cs if cs in quotes else _fyers_symbol(cs)
                if k in quotes:
                    r["call_ltp"] = quotes[k].get("ltp")
            if ps:
                k = ps if ps in quotes else _fyers_symbol(ps)
                if k in quotes:
                    r["put_ltp"] = quotes[k].get("ltp")
    except Exception:
        pass


def _transform_fyers_chain_to_rows(raw: list[dict]) -> list[dict]:
    """Group Fyers CE/PE rows by strike into our options_chain schema."""
    grouped: dict[float, dict] = {}
    for row in raw:
        strike = float(row.get("strike_price", 0))
        opt_type = str(row.get("option_type", "")).upper()
        if strike not in grouped:
            grouped[strike] = {
                "strike_price": strike,
                "call_token": None,
                "call_symbol": None,
                "call_oi": None,
                "call_iv": None,
                "put_token": None,
                "put_symbol": None,
                "put_oi": None,
                "put_iv": None,
                "put_call_ratio": None,
                "lot_size": 1,
            }
        token = row.get("token") or row.get("symbol")
        oi = row.get("oi") or 0
        iv = row.get("iv")
        symbol = row.get("symbol", "")
        ltp_val = row.get("ltp")
        if opt_type == "CE":
            grouped[strike]["call_token"] = token
            grouped[strike]["call_symbol"] = symbol
            grouped[strike]["call_oi"] = int(oi) if oi is not None else None
            grouped[strike]["call_iv"] = float(iv) if iv is not None else None
            grouped[strike]["call_ltp"] = float(ltp_val) if ltp_val is not None else None
        else:
            grouped[strike]["put_token"] = token
            grouped[strike]["put_symbol"] = symbol
            grouped[strike]["put_oi"] = int(oi) if oi is not None else None
            grouped[strike]["put_iv"] = float(iv) if iv is not None else None
            grouped[strike]["put_ltp"] = float(ltp_val) if ltp_val is not None else None
    for row in grouped.values():
        co = row.get("call_oi") or 0
        po = row.get("put_oi") or 0
        row["put_call_ratio"] = round(po / co, 4) if co > 0 else None
    return sorted(grouped.values(), key=lambda x: x["strike_price"])


class OptionsChainService:
    def __init__(self, fyers_client: FyersClient | None = None) -> None:
        self.fyers_client = fyers_client or FyersClient()
        self._session_factory: sessionmaker[Session] | None = None

    def set_session_factory(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def refresh_chain(self, *, underlying: str, expiry: str) -> int:
        if self._session_factory is None:
            return 0
        try:
            from app.services.fyers_data import get_option_chain
            from app.services.fyers_token_store import load_token
            if load_token():
                raw = get_option_chain(underlying=underlying, expiry=expiry)
                if raw:
                    chain_rows = _transform_fyers_chain_to_rows(raw)
                    repo = OptionsChainRepository(self._session_factory)
                    return repo.upsert_chain(underlying=underlying.upper(), expiry=expiry, rows=chain_rows)
        except Exception:
            pass
        records = await self.fyers_client.fetch_scrip_master()
        chain_rows = self.fyers_client.build_options_chain(records, underlying=underlying, expiry=expiry)
        repo = OptionsChainRepository(self._session_factory)
        return repo.upsert_chain(underlying=underlying.upper(), expiry=expiry, rows=chain_rows)

    def get_chain(self, *, underlying: str, expiry: str, limit: int = 200) -> list[dict]:
        if self._session_factory is None:
            return []
        repo = OptionsChainRepository(self._session_factory)
        rows = repo.list_chain(underlying=underlying.upper(), expiry=expiry, limit=limit)
        _enrich_chain_with_ltp(rows)
        return rows

    def get_chain_metrics(self, *, underlying: str, expiry: str) -> dict:
        if self._session_factory is None:
            return {
                "underlying": underlying.upper(),
                "expiry": expiry,
                "strikes": 0,
                "total_call_oi": 0,
                "total_put_oi": 0,
                "put_call_ratio": None,
                "total_oi_change": 0,
            }
        repo = OptionsChainRepository(self._session_factory)
        return repo.get_chain_metrics(underlying=underlying.upper(), expiry=expiry)


options_chain_service = OptionsChainService()
