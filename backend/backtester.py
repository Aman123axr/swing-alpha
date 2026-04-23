from __future__ import annotations
import numpy as np
import pandas as pd
from indicators import add_emas, find_swing_lows
from pattern_detector import detect_vcp, detect_bull_flag

MIN_HISTORY = 65


def _entry_price(vcp: dict, bull_flag: dict, current_price: float) -> float:
    if vcp["detected"] and vcp.get("breakout_level"):
        return float(vcp["breakout_level"])
    if bull_flag["detected"] and bull_flag.get("breakout_level"):
        return float(bull_flag["breakout_level"])
    if vcp["detected"] and vcp.get("resistance_level"):
        return float(vcp["resistance_level"])
    if bull_flag["detected"] and bull_flag.get("resistance_level"):
        return float(bull_flag["resistance_level"])
    return current_price


def _stop_loss(df: pd.DataFrame, ema_20_series: pd.Series) -> float:
    closes = df["Close"].values
    current_price = float(closes[-1])
    e20 = float(ema_20_series.iloc[-1])
    lows = find_swing_lows(pd.Series(closes), window=5)
    last_swing_low = float(closes[lows[-1]]) if lows else current_price * 0.95
    return max(e20 * 0.99, last_swing_low * 0.995)


def _simulate_trade(
    forward: pd.DataFrame,
    actual_entry: float,
    sl: float,
    target: float,
    max_hold: int,
) -> dict:
    n = min(max_hold, len(forward))
    for j in range(n):
        row = forward.iloc[j]
        low, high = float(row["Low"]), float(row["High"])
        exit_date = str(forward.index[j].date())
        # Both hit intraday → worst case: SL fills first
        if low <= sl:
            return {
                "exit_price": round(sl, 2), "exit_date": exit_date,
                "exit_reason": "stop_loss", "hold_days": j + 1,
                "pnl_pct": round((sl - actual_entry) / actual_entry * 100, 2),
            }
        if high >= target:
            return {
                "exit_price": round(target, 2), "exit_date": exit_date,
                "exit_reason": "target", "hold_days": j + 1,
                "pnl_pct": round((target - actual_entry) / actual_entry * 100, 2),
            }
    last_close = float(forward["Close"].iloc[n - 1])
    return {
        "exit_price": round(last_close, 2),
        "exit_date": str(forward.index[n - 1].date()),
        "exit_reason": "time_exit", "hold_days": n,
        "pnl_pct": round((last_close - actual_entry) / actual_entry * 100, 2),
    }


def _compute_stats(trades: list) -> dict:
    if not trades:
        return {
            "total_trades": 0, "wins": 0, "losses": 0, "win_rate": 0.0,
            "avg_return_pct": 0.0, "avg_win_pct": 0.0, "avg_loss_pct": 0.0,
            "total_return_pct": 0.0, "expectancy": 0.0, "max_drawdown_pct": 0.0,
        }
    returns = [t["pnl_pct"] for t in trades]
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r <= 0]
    win_rate = len(wins) / len(trades) * 100
    avg_win = float(np.mean(wins)) if wins else 0.0
    avg_loss = float(np.mean(losses)) if losses else 0.0
    expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)
    cum = np.cumsum(returns)
    peak = np.maximum.accumulate(cum)
    max_dd = float(np.min(cum - peak)) if len(cum) > 0 else 0.0
    return {
        "total_trades": len(trades), "wins": len(wins), "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "avg_return_pct": round(float(np.mean(returns)), 2),
        "avg_win_pct": round(avg_win, 2),
        "avg_loss_pct": round(avg_loss, 2),
        "total_return_pct": round(float(sum(returns)), 2),
        "expectancy": round(expectancy, 2),
        "max_drawdown_pct": round(max_dd, 2),
    }


def backtest_ticker(
    ticker: str,
    df: pd.DataFrame,
    rr_ratio: float = 2.0,
    max_hold_days: int = 20,
    max_loss_pct: float = 5.0,
    max_profit_pct: float = 15.0,
    breakout_only: bool = False,
) -> dict:
    """
    Walk-forward backtest with per-trade risk controls:
      - max_loss_pct: hard stop override if calculated SL is too loose
      - max_profit_pct: take-profit ceiling regardless of R:R target
      - breakout_only: only enter when price has already broken out (higher conviction)
    """
    trades = []
    df = add_emas(df)

    i = MIN_HISTORY
    while i < len(df) - max_hold_days - 1:
        hist = df.iloc[:i]
        current_price = float(hist["Close"].iloc[-1])
        ema_20_series = hist["ema_20"]

        vcp = detect_vcp(hist)
        bull_flag = detect_bull_flag(hist, ema_20_series)

        if not (vcp["detected"] or bull_flag["detected"]):
            i += 1
            continue

        # Breakout-only filter: skip pre-breakout setups
        if breakout_only:
            has_breakout = vcp.get("breakout_detected") or bull_flag.get("breakout_detected")
            if not has_breakout:
                i += 1
                continue

        entry = _entry_price(vcp, bull_flag, current_price)
        sl = _stop_loss(hist, ema_20_series)

        if entry <= 0:
            i += 1
            continue

        # Use next-day open as actual entry
        forward = df.iloc[i:]
        actual_entry = float(forward["Open"].iloc[0])

        # --- Risk controls applied to actual entry ---

        # 1. Max loss cap: tighten the stop loss if it would exceed max_loss_pct
        hard_sl = actual_entry * (1 - max_loss_pct / 100)
        sl = max(sl, hard_sl)  # higher price = tighter (less loss)

        risk = actual_entry - sl
        if risk <= 0:
            i += 1
            continue

        # 2. Max profit cap: ceiling on the target regardless of R:R
        rr_target = actual_entry + rr_ratio * risk
        hard_target = actual_entry * (1 + max_profit_pct / 100)
        target = min(rr_target, hard_target)

        # Skip if target is not meaningfully above entry (cap too tight vs stop)
        if target <= actual_entry:
            i += 1
            continue

        pattern_type = "VCP" if vcp["detected"] else "Bull Flag"
        outcome = _simulate_trade(forward, actual_entry, sl, target, max_hold_days)

        trades.append({
            "signal_date": str(hist.index[-1].date()),
            "entry_price": round(actual_entry, 2),
            "stop_loss": round(sl, 2),
            "target": round(target, 2),
            "pattern_type": pattern_type,
            "max_loss_pct": round((actual_entry - sl) / actual_entry * 100, 2),
            "max_profit_pct": round((target - actual_entry) / actual_entry * 100, 2),
            **outcome,
        })

        i += outcome["hold_days"] + 1

    return {"ticker": ticker, "trades": trades, "stats": _compute_stats(trades)}
