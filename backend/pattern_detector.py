import numpy as np
import pandas as pd
from typing import List
from indicators import find_swing_highs, find_swing_lows


def detect_vcp(df: pd.DataFrame) -> dict:
    """
    Volatility Contraction Pattern:
    - 3+ consecutive contractions with decreasing range
    - Volume declining across contractions
    - Price tightening near resistance (within 8%)
    - Final contraction range < 8%
    """
    NO_PATTERN = {"detected": False, "contraction_count": 0, "resistance_level": None,
                  "breakout_detected": False, "breakout_level": None, "last_range_pct": None}

    data = df.tail(60).reset_index(drop=True)
    if len(data) < 20:
        return NO_PATTERN

    closes = data["Close"]
    highs = data["High"].values
    lows = data["Low"].values
    volumes = data["Volume"].values

    swing_high_indices = find_swing_highs(closes, window=5)
    swing_low_indices = find_swing_lows(closes, window=5)

    if len(swing_high_indices) < 2 or len(swing_low_indices) < 2:
        return NO_PATTERN

    # Build contraction segments: each swing high paired with next swing low after it
    contractions = []
    for hi in swing_high_indices:
        for li in swing_low_indices:
            if li > hi:
                high_price = highs[hi]
                low_price = lows[li]
                if high_price <= 0:
                    continue
                range_pct = (high_price - low_price) / high_price
                seg_volumes = volumes[hi: li + 1]
                avg_vol = float(seg_volumes.mean()) if len(seg_volumes) > 0 else 0.0
                contractions.append({
                    "high_idx": hi, "low_idx": li,
                    "high_price": high_price, "low_price": low_price,
                    "range_pct": range_pct, "avg_vol": avg_vol,
                })
                break  # only first low after each high

    if len(contractions) < 3:
        return NO_PATTERN

    # Take the last 5 contractions for analysis
    contractions = contractions[-5:]

    # Count consecutive shrinking range
    shrink_count = 0
    for i in range(1, len(contractions)):
        if contractions[i]["range_pct"] < contractions[i - 1]["range_pct"]:
            shrink_count += 1

    if shrink_count < 2:
        return NO_PATTERN

    # Volume must trend down: last contraction avg vol < first contraction avg vol by 20%+
    first_vol = contractions[0]["avg_vol"]
    last_vol = contractions[-1]["avg_vol"]
    if first_vol > 0 and last_vol >= first_vol * 0.8:
        return NO_PATTERN

    # Resistance = 60-candle high
    resistance = float(data["High"].max())

    # Latest contraction high must be within 8% of resistance
    last_contraction = contractions[-1]
    price_vs_resistance = last_contraction["high_price"] / resistance
    if price_vs_resistance < 0.92:
        return NO_PATTERN

    # Final contraction range must be tight (< 8%)
    if last_contraction["range_pct"] > 0.08:
        return NO_PATTERN

    current_price = float(closes.iloc[-1])
    breakout_detected = current_price >= resistance * 0.995

    return {
        "detected": True,
        "contraction_count": shrink_count + 1,
        "resistance_level": round(resistance, 2),
        "breakout_detected": breakout_detected,
        "breakout_level": round(resistance, 2),
        "last_range_pct": round(last_contraction["range_pct"] * 100, 2),
    }


def detect_bull_flag(df: pd.DataFrame, ema_20: pd.Series) -> dict:
    """
    Bullish Flag Pattern:
    - Flagpole: ≥8% gain over 5-15 candles
    - Consolidation: lower volume, price above 20 EMA (max 1 violation)
    - Channel: flat or slightly downward slope (≤+0.3% per candle)
    - Retracement from flagpole high ≤ 50%
    """
    NO_PATTERN = {"detected": False, "pole_gain_pct": None, "consol_depth_pct": None,
                  "resistance_level": None, "breakout_detected": False, "breakout_level": None}

    if len(df) < 20:
        return NO_PATTERN

    closes = df["Close"].values
    volumes = df["Volume"].values
    ema_vals = ema_20.values
    n = len(closes)

    # Find most recent flagpole (scan from end backward)
    pole_end = None
    pole_start = None
    pole_gain = 0.0

    for end in range(n - 1, 14, -1):
        for window in range(5, 16):
            start = end - window
            if start < 0:
                continue
            if closes[start] <= 0:
                continue
            gain = (closes[end] - closes[start]) / closes[start]
            if gain >= 0.08:
                pole_end = end
                pole_start = start
                pole_gain = gain
                break
        if pole_end is not None:
            break

    if pole_end is None or pole_end >= n - 3:
        return NO_PATTERN

    # Consolidation is everything after the pole top
    consol_start = pole_end + 1
    consol_end = n - 1
    consol_len = consol_end - consol_start + 1

    if consol_len < 3:
        return NO_PATTERN

    consol_closes = closes[consol_start: consol_end + 1]
    consol_volumes = volumes[consol_start: consol_end + 1]
    pole_volumes = volumes[pole_start: pole_end + 1]

    avg_pole_vol = float(pole_volumes.mean())
    avg_consol_vol = float(consol_volumes.mean())

    # Volume must drop in consolidation
    if avg_pole_vol > 0 and avg_consol_vol >= avg_pole_vol:
        return NO_PATTERN

    # Price must stay above 20 EMA (max 1 close below)
    ema_consol = ema_vals[consol_start: consol_end + 1]
    violations = int(np.sum(consol_closes < ema_consol))
    if violations > 1:
        return NO_PATTERN

    # Channel slope: flat or negative (≤ +0.3% per candle)
    if consol_len >= 2:
        slope = float(np.polyfit(range(consol_len), consol_closes, 1)[0])
        normalized_slope = slope / consol_closes[0] if consol_closes[0] > 0 else 0
        if normalized_slope > 0.003:
            return NO_PATTERN

    # Retracement depth ≤ 50% of flagpole high
    pole_high = float(closes[pole_end])
    consol_low = float(consol_closes.min())
    if pole_high > 0:
        depth_pct = (pole_high - consol_low) / pole_high
        if depth_pct > 0.50:
            return NO_PATTERN
    else:
        depth_pct = 0.0

    consol_high = float(consol_closes.max())
    current_price = float(closes[-1])
    breakout_detected = current_price >= consol_high * 0.995

    return {
        "detected": True,
        "pole_gain_pct": round(pole_gain * 100, 2),
        "consol_depth_pct": round(depth_pct * 100, 2),
        "resistance_level": round(consol_high, 2),
        "breakout_detected": breakout_detected,
        "breakout_level": round(consol_high, 2),
    }
