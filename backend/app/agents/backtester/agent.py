"""Backtester agent: historical data, entry/exit logic, P&L, Sharpe, max drawdown, win rate."""

from __future__ import annotations

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.agents.backtester.engine import run_backtest
from app.screener.scanner import ConditionGroup, IndicatorCondition
from app.services.market_data import market_data_service


class BacktesterAgent(BaseAgent):
    """Backtests strategies on historical data."""

    name = "backtester"

    async def run(self, ctx: AgentContext) -> AgentResult:
        rules = ctx.request_payload.get("rules") or []
        groups_raw = ctx.request_payload.get("groups") or []
        timeframe = ctx.request_payload.get("timeframe") or "5m"
        underlying = ctx.request_payload.get("underlying") or "NIFTY"
        hold_bars = int(ctx.request_payload.get("hold_bars") or 5)
        candle_limit = int(ctx.request_payload.get("candle_limit") or 200)
        max_tokens = int(ctx.request_payload.get("max_tokens") or 10)

        scanner_out = ctx.outputs.get("scanner", {})
        matched = scanner_out.get("matched", [])
        total = scanner_out.get("total", 0)

        if groups_raw:
            groups = [
                ConditionGroup(
                    logical_operator=g.get("logical_operator", "AND"),
                    conditions=[
                        IndicatorCondition(
                            field=r["field"],
                            operator=r["operator"],
                            value=float(r["value"]),
                        )
                        for r in g.get("rules", [])
                    ],
                )
                for g in groups_raw
            ]
        elif rules:
            groups = [
                ConditionGroup(
                    logical_operator="AND",
                    conditions=[
                        IndicatorCondition(
                            field=r["field"],
                            operator=r["operator"],
                            value=float(r["value"]),
                        )
                        for r in rules
                    ],
                )
            ]
        else:
            groups = [
                ConditionGroup(
                    logical_operator="AND",
                    conditions=[
                        IndicatorCondition(field="rsi_14", operator="<", value=35.0),
                    ],
                )
            ]

        all_trades: list[dict] = []
        total_pnl = 0.0
        total_sharpe = 0.0
        total_max_dd = 0.0
        total_wins = 0
        total_trade_count = 0
        tokens_tested = 0

        for m in matched[:max_tokens]:
            token = m.get("token", "")
            if not token:
                continue
            candles = market_data_service.get_chart(
                token=token,
                timeframe=timeframe,
                limit=candle_limit,
            )
            if len(candles) < 30:
                continue
            trades, pnl, sharpe, max_dd, win_rate, _ = run_backtest(
                token=token,
                candles=candles,
                groups=groups,
                hold_bars=hold_bars,
            )
            tokens_tested += 1
            total_pnl += pnl
            total_sharpe += sharpe
            total_max_dd += max_dd
            total_trade_count += len(trades)
            total_wins += sum(1 for t in trades if t.pnl > 0)
            for t in trades:
                all_trades.append({
                    "token": t.token,
                    "entry_bar": t.entry_bar,
                    "exit_bar": t.exit_bar,
                    "entry_price": round(t.entry_price, 2),
                    "exit_price": round(t.exit_price, 2),
                    "pnl": round(t.pnl, 2),
                    "entry_reason": t.entry_reason,
                    "exit_reason": t.exit_reason,
                })

        avg_sharpe = total_sharpe / tokens_tested if tokens_tested else 0.0
        win_rate_final = total_wins / total_trade_count if total_trade_count else 0.0

        return AgentResult(
            agent_name=self.name,
            success=True,
            output={
                "pnl": round(total_pnl, 2),
                "sharpe": round(avg_sharpe, 4),
                "max_drawdown": round(total_max_dd, 2),
                "win_rate": round(win_rate_final, 4),
                "total_trades": total_trade_count,
                "tokens_tested": tokens_tested,
                "trades": all_trades[:50],
                "underlying": underlying,
                "timeframe": timeframe,
            },
        )


backtester_agent = BacktesterAgent()
