"""Optimizer agent: grid search, walk-forward analysis, best params selection."""

from __future__ import annotations

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.agents.backtester.engine import run_backtest
from app.screener.scanner import ConditionGroup, IndicatorCondition
from app.services.market_data import market_data_service


class OptimizerAgent(BaseAgent):
    """Optimizes strategy parameters via grid search and walk-forward analysis."""

    name = "optimizer"

    async def run(self, ctx: AgentContext) -> AgentResult:
        backtest_out = ctx.outputs.get("backtester", {})
        sharpe = backtest_out.get("sharpe", 0.0)
        win_rate = backtest_out.get("win_rate", 0.0)
        pnl = backtest_out.get("pnl", 0.0)
        trades = backtest_out.get("trades", [])
        tokens_tested = backtest_out.get("tokens_tested", 0)

        param_space = ctx.request_payload.get("param_space") or {}
        do_walk_forward = bool(ctx.request_payload.get("walk_forward") or False)
        timeframe = ctx.request_payload.get("timeframe") or "5m"
        underlying = ctx.request_payload.get("underlying") or "NIFTY"
        max_tokens = int(ctx.request_payload.get("max_tokens") or 5)

        scanner_out = ctx.outputs.get("scanner", {})
        matched = scanner_out.get("matched", [])[:max_tokens]

        best_params = ctx.request_payload.get("rules", [{}])[0] if ctx.request_payload.get("rules") else {}
        best_sharpe = sharpe
        best_win_rate = win_rate
        best_pnl = pnl
        iterations = 1

        if do_walk_forward and param_space and matched:
            rsi_thresholds = param_space.get("rsi_thresholds", [30, 35, 40])
            hold_bars_list = param_space.get("hold_bars", [3, 5, 8])
            wf_results: list[dict] = []

            for rsi_val in rsi_thresholds:
                for hold in hold_bars_list:
                    groups = [
                        ConditionGroup(
                            logical_operator="AND",
                            conditions=[
                                IndicatorCondition(field="rsi_14", operator="<", value=float(rsi_val)),
                            ],
                        )
                    ]
                    total_pnl_wf = 0.0
                    total_sharpe_wf = 0.0
                    total_wins = 0
                    total_trades_wf = 0
                    tested = 0

                    for m in matched:
                        token = m.get("token", "")
                        if not token:
                            continue
                        candles = market_data_service.get_chart(
                            token=token,
                            timeframe=timeframe,
                            limit=200,
                        )
                        if len(candles) < 30:
                            continue
                        trade_list, pnl_wf, sharpe_wf, _, _, n_trades = run_backtest(
                            token=token,
                            candles=candles,
                            groups=groups,
                            hold_bars=hold,
                        )
                        total_pnl_wf += pnl_wf
                        total_sharpe_wf += sharpe_wf
                        tested += 1
                        total_wins += sum(1 for t in trade_list if t.pnl > 0)
                        total_trades_wf += n_trades

                    if tested > 0:
                        avg_sharpe = total_sharpe_wf / tested
                        wf_results.append({
                            "rsi_threshold": rsi_val,
                            "hold_bars": hold,
                            "sharpe": round(avg_sharpe, 4),
                            "pnl": round(total_pnl_wf, 2),
                        })
                        wf_win_rate = total_wins / total_trades_wf if total_trades_wf else 0.0
                        if avg_sharpe > best_sharpe:
                            best_sharpe = avg_sharpe
                            best_params = {"rsi_threshold": rsi_val, "hold_bars": hold}
                            best_pnl = total_pnl_wf
                            best_win_rate = wf_win_rate

            iterations = len(rsi_thresholds) * len(hold_bars_list)
            if wf_results:
                best_result = max(wf_results, key=lambda x: x["sharpe"])
                best_params = {
                    "rsi_threshold": best_result["rsi_threshold"],
                    "hold_bars": best_result["hold_bars"],
                }
                best_sharpe = best_result["sharpe"]
                best_pnl = best_result["pnl"]

        return AgentResult(
            agent_name=self.name,
            success=True,
            output={
                "best_params": best_params,
                "best_sharpe": round(best_sharpe, 4),
                "best_win_rate": round(best_win_rate, 4),
                "best_pnl": round(best_pnl, 2),
                "param_space": param_space,
                "iterations": iterations,
                "walk_forward": do_walk_forward,
            },
        )


optimizer_agent = OptimizerAgent()
