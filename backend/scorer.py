import pandas as pd
from typing import Tuple
from indicators import compute_avg_volume, find_swing_lows
from pattern_detector import (
    detect_vcp, detect_bull_flag, detect_cup_with_handle,
    detect_flat_base, detect_double_bottom, detect_ascending_triangle,
    detect_base_on_base, detect_high_tight_flag,
)

# Pattern detection priority (highest conviction first)
_PATTERN_PRIORITY = [
    ("high_tight_flag", "High Tight Flag",  3.0),
    ("cup_with_handle",  "Cup with Handle", 3.0),
    ("vcp",              "VCP",             3.0),
    ("double_bottom",    "Double Bottom",   2.0),
    ("bull_flag",        "Bull Flag",       2.0),
    ("ascending_triangle", "Ascending Triangle", 2.0),
    ("flat_base",        "Flat Base",       1.5),
    ("base_on_base",     "Base on Base",    1.5),
]


def _score_trend(current_price: float, e20: float, e44: float, e200: float) -> int:
    full_trend = (e20 > e44 > e200) and (current_price > e20)
    if full_trend:
        return 3
    partial_trend = (e20 > e200) or (current_price > e44)
    if partial_trend:
        return 2
    return 0


def _score_pattern(patterns: dict, current_price: float, e20: float) -> Tuple[float, str]:
    for key, label, score in _PATTERN_PRIORITY:
        if patterns[key]["detected"]:
            return score, label
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
    patterns: dict,
    ema_20_series: pd.Series,
) -> Tuple[float, float]:
    closes = df["Close"].values
    current_price = float(closes[-1])
    e20_current = float(ema_20_series.iloc[-1])

    # Entry: use resistance/pivot from highest-priority detected pattern
    entry = current_price
    for key, _, _ in _PATTERN_PRIORITY:
        p = patterns[key]
        if p["detected"]:
            if p.get("breakout_detected") and p.get("breakout_level"):
                entry = p["breakout_level"]
            elif p.get("resistance_level"):
                entry = p["resistance_level"]
            break

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

    patterns = {
        "vcp":                detect_vcp(df),
        "bull_flag":          detect_bull_flag(df, ema_20),
        "cup_with_handle":    detect_cup_with_handle(df),
        "flat_base":          detect_flat_base(df),
        "double_bottom":      detect_double_bottom(df),
        "ascending_triangle": detect_ascending_triangle(df),
        "base_on_base":       detect_base_on_base(df),
        "high_tight_flag":    detect_high_tight_flag(df),
    }

    trend_score = _score_trend(current_price, e20, e44, e200)
    pattern_score, pattern_type = _score_pattern(patterns, current_price, e20)
    volume_score = _score_volume(df)
    growth_score, debt_score, inst_score, fund_score = _score_fundamentals(fundamentals)

    total_score = trend_score + pattern_score + volume_score + fund_score

    if total_score >= 8:
        category = "High Conviction"
    elif total_score >= 6:
        category = "Good Swing"
    else:
        category = "Avoid"

    entry, stop_loss = _compute_entry_sl(df, patterns, ema_20)

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
        # individual pattern results
        "vcp":                patterns["vcp"],
        "bull_flag":          patterns["bull_flag"],
        "cup_with_handle":    patterns["cup_with_handle"],
        "flat_base":          patterns["flat_base"],
        "double_bottom":      patterns["double_bottom"],
        "ascending_triangle": patterns["ascending_triangle"],
        "base_on_base":       patterns["base_on_base"],
        "high_tight_flag":    patterns["high_tight_flag"],
        "fifty_two_week_high": fundamentals.get("fifty_two_week_high"),
    }
