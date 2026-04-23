import pandas as pd
from typing import Tuple
from indicators import compute_avg_volume, find_swing_lows
from pattern_detector import detect_vcp, detect_bull_flag


def _score_trend(current_price: float, e20: float, e44: float, e200: float) -> int:
    full_trend = (e20 > e44 > e200) and (current_price > e20)
    if full_trend:
        return 3
    partial_trend = (e20 > e200) or (current_price > e44)
    if partial_trend:
        return 2
    return 0


def _score_pattern(vcp: dict, flag: dict, current_price: float, e20: float) -> Tuple[float, str]:
    if vcp["detected"]:
        return 2, "VCP"
    if flag["detected"]:
        return 2, "Bull Flag"
    if current_price > e20:
        return 1, "Loose Structure"
    return 0, "None"


def _score_volume(df: pd.DataFrame) -> int:
    avg_vol = compute_avg_volume(df, lookback=20)
    if avg_vol <= 0:
        return 0
    recent_vol = float(df["Volume"].iloc[-1])
    ratio = recent_vol / avg_vol
    if ratio >= 1.5:
        return 2
    if ratio >= 1.0:
        return 1
    return 0


def _score_fundamentals(fundamentals: dict) -> Tuple[float, float, float, float]:
    rev_growth = fundamentals.get("revenue_growth") or 0.0
    earn_growth = fundamentals.get("earnings_growth") or 0.0
    raw_de = fundamentals.get("debt_to_equity")
    # yfinance returns D/E as a percentage value (e.g. 45.2 → actual ratio 0.452)
    debt_equity = (raw_de / 100.0) if raw_de is not None else 999.0
    inst_holding = fundamentals.get("held_percent_institutions") or 0.0

    if rev_growth >= 0.15 and earn_growth >= 0.15:
        growth_score = 1.5
    elif rev_growth >= 0.08 or earn_growth >= 0.08:
        growth_score = 1.0
    else:
        growth_score = 0.0

    debt_score = 1.0 if debt_equity < 0.5 else 0.0
    inst_score = 0.5 if inst_holding > 0.01 else 0.0

    return growth_score, debt_score, inst_score, growth_score + debt_score + inst_score


def _compute_entry_sl(
    df: pd.DataFrame,
    vcp: dict,
    flag: dict,
    ema_20_series: pd.Series,
) -> Tuple[float, float]:
    closes = df["Close"].values
    current_price = float(closes[-1])
    e20_current = float(ema_20_series.iloc[-1])

    # Entry
    if vcp["detected"] and vcp["breakout_detected"]:
        entry = vcp["breakout_level"]
    elif flag["detected"] and flag["breakout_detected"]:
        entry = flag["breakout_level"]
    elif vcp["detected"]:
        entry = vcp["resistance_level"]
    elif flag["detected"]:
        entry = flag["resistance_level"]
    else:
        entry = current_price

    # Stop loss: higher of (1% below 20 EMA) or (0.5% below last swing low)
    swing_low_indices = find_swing_lows(pd.Series(closes), window=5)
    if swing_low_indices:
        last_swing_low = float(closes[swing_low_indices[-1]])
    else:
        last_swing_low = current_price * 0.95

    sl_ema = e20_current * 0.99
    sl_swing = last_swing_low * 0.995
    stop_loss = max(sl_ema, sl_swing)

    return round(float(entry), 2), round(float(stop_loss), 2)


def score_stock(ticker: str, df: pd.DataFrame, fundamentals: dict) -> dict:
    from indicators import add_emas

    df = add_emas(df)

    ema_20 = df["ema_20"]
    ema_44 = df["ema_44"]
    ema_200 = df["ema_200"]

    current_price = float(df["Close"].iloc[-1])
    e20 = float(ema_20.iloc[-1])
    e44 = float(ema_44.iloc[-1])
    e200 = float(ema_200.iloc[-1])

    vcp = detect_vcp(df)
    flag = detect_bull_flag(df, ema_20)

    trend_score = _score_trend(current_price, e20, e44, e200)
    pattern_score, pattern_type = _score_pattern(vcp, flag, current_price, e20)
    volume_score = _score_volume(df)
    growth_score, debt_score, inst_score, fund_score = _score_fundamentals(fundamentals)

    total_score = trend_score + pattern_score + volume_score + fund_score

    if total_score >= 8:
        category = "High Conviction"
    elif total_score >= 6:
        category = "Good Swing"
    else:
        category = "Avoid"

    entry, stop_loss = _compute_entry_sl(df, vcp, flag, ema_20)

    rev_growth = fundamentals.get("revenue_growth") or 0.0
    earn_growth = fundamentals.get("earnings_growth") or 0.0
    raw_de = fundamentals.get("debt_to_equity")
    debt_equity_ratio = (raw_de / 100.0) if raw_de is not None else None
    inst_holding = fundamentals.get("held_percent_institutions") or 0.0

    return {
        "ticker": ticker,
        "short_name": fundamentals.get("short_name") or ticker,
        "current_price": fundamentals.get("current_price") or current_price,
        "day_change_pct": round(fundamentals["day_change_pct"], 2) if fundamentals.get("day_change_pct") is not None else None,
        "total_score": round(total_score, 1),
        "trend_score": trend_score,
        "pattern_score": pattern_score,
        "volume_score": volume_score,
        "fund_score": round(fund_score, 1),
        "pattern_type": pattern_type,
        "category": category,
        "entry": entry,
        "stop_loss": stop_loss,
        "ema_20": round(e20, 2),
        "ema_44": round(e44, 2),
        "ema_200": round(e200, 2),
        "revenue_growth_pct": round(rev_growth * 100, 1),
        "earnings_growth_pct": round(earn_growth * 100, 1),
        "debt_to_equity": round(debt_equity_ratio, 2) if debt_equity_ratio is not None else None,
        "institutional_holding_pct": round(inst_holding * 100, 1),
        "vcp": vcp,
        "bull_flag": flag,
        "fifty_two_week_high": fundamentals.get("fifty_two_week_high"),
    }
