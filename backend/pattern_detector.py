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
                break

    if len(contractions) < 3:
        return NO_PATTERN

    contractions = contractions[-5:]

    shrink_count = 0
    for i in range(1, len(contractions)):
        if contractions[i]["range_pct"] < contractions[i - 1]["range_pct"]:
            shrink_count += 1

    if shrink_count < 2:
        return NO_PATTERN

    first_vol = contractions[0]["avg_vol"]
    last_vol = contractions[-1]["avg_vol"]
    if first_vol > 0 and last_vol >= first_vol * 0.8:
        return NO_PATTERN

    resistance = float(data["High"].max())

    last_contraction = contractions[-1]
    price_vs_resistance = last_contraction["high_price"] / resistance
    if price_vs_resistance < 0.92:
        return NO_PATTERN

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

    if avg_pole_vol > 0 and avg_consol_vol >= avg_pole_vol:
        return NO_PATTERN

    ema_consol = ema_vals[consol_start: consol_end + 1]
    violations = int(np.sum(consol_closes < ema_consol))
    if violations > 1:
        return NO_PATTERN

    if consol_len >= 2:
        slope = float(np.polyfit(range(consol_len), consol_closes, 1)[0])
        normalized_slope = slope / consol_closes[0] if consol_closes[0] > 0 else 0
        if normalized_slope > 0.003:
            return NO_PATTERN

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


def detect_cup_with_handle(df: pd.DataFrame) -> dict:
    """
    Cup with Handle (Minervini / O'Neil):
    - U-shaped decline and recovery over 30-200 candles
    - Cup depth 15-50% from left high
    - Right side recovers to ≥ 90% of left high (not a V-shape: bottom in middle 20-80%)
    - Handle: 3-25 candle pullback of 3-15%, volume dry-up
    - Pivot = handle high
    """
    NO_PATTERN = {"detected": False, "cup_depth_pct": None, "handle_depth_pct": None,
                  "resistance_level": None, "breakout_detected": False, "breakout_level": None}

    data = df.tail(200).reset_index(drop=True)
    n = len(data)
    if n < 50:
        return NO_PATTERN

    closes = data["Close"].values
    highs = data["High"].values
    lows = data["Low"].values
    volumes = data["Volume"].values

    # Look for cup left high in first 80% of data
    search_bound = max(30, int(n * 0.80))
    swing_high_idxs = find_swing_highs(pd.Series(highs[:search_bound]), window=10)
    if not swing_high_idxs:
        return NO_PATTERN

    for cup_left_idx in reversed(swing_high_idxs):
        cup_left_high = highs[cup_left_idx]

        # Bottom: min in [cup_left+5 … cup_left + 70% of remaining], leave ≥6 bars for handle
        remaining = n - cup_left_idx
        bottom_end = cup_left_idx + max(10, int(remaining * 0.70))
        bottom_end = min(bottom_end, n - 6)
        if bottom_end <= cup_left_idx + 5:
            continue

        bottom_offset = int(np.argmin(lows[cup_left_idx: bottom_end + 1]))
        bottom_idx = cup_left_idx + bottom_offset
        bottom_price = lows[bottom_idx]

        if cup_left_high <= 0:
            continue
        cup_depth = (cup_left_high - bottom_price) / cup_left_high
        if not (0.15 <= cup_depth <= 0.50):
            continue

        # Right side high (leave ≥3 bars for handle at the end)
        right_end = n - 3
        if right_end <= bottom_idx + 5:
            continue

        right_highs_slice = highs[bottom_idx: right_end + 1]
        right_high_offset = int(np.argmax(right_highs_slice))
        right_high_idx = bottom_idx + right_high_offset
        right_high_price = right_highs_slice[right_high_offset]

        # Right side must recover to ≥ 90% of cup left high
        if right_high_price < cup_left_high * 0.90:
            continue

        # U-shape check: bottom must sit in middle 20-80% of cup span
        cup_span = right_high_idx - cup_left_idx
        if cup_span < 20:
            continue
        bottom_rel = (bottom_idx - cup_left_idx) / cup_span
        if not (0.20 <= bottom_rel <= 0.80):
            continue

        # Handle: bars from right_high_idx+1 to end
        handle_start = right_high_idx + 1
        if handle_start >= n:
            continue
        handle_len = n - handle_start
        if not (3 <= handle_len <= 25):
            continue

        handle_lows_slice = lows[handle_start:]
        handle_highs_slice = highs[handle_start:]
        handle_vols_slice = volumes[handle_start:]

        handle_low = float(handle_lows_slice.min())
        handle_high = float(handle_highs_slice.max())
        handle_depth = (right_high_price - handle_low) / right_high_price if right_high_price > 0 else 0

        if not (0.03 <= handle_depth <= 0.15):
            continue

        # Volume dry-up in handle vs cup right side
        cup_right_avg_vol = float(volumes[bottom_idx: right_high_idx + 1].mean())
        handle_avg_vol = float(handle_vols_slice.mean()) if len(handle_vols_slice) > 0 else 0.0
        if cup_right_avg_vol > 0 and handle_avg_vol >= cup_right_avg_vol:
            continue

        pivot = handle_high
        current_price = float(closes[-1])
        breakout = current_price >= pivot * 0.995

        return {
            "detected": True,
            "cup_depth_pct": round(cup_depth * 100, 2),
            "handle_depth_pct": round(handle_depth * 100, 2),
            "resistance_level": round(pivot, 2),
            "breakout_detected": breakout,
            "breakout_level": round(pivot, 2),
        }

    return NO_PATTERN


def detect_flat_base(df: pd.DataFrame) -> dict:
    """
    Flat Base / Tight Base:
    - Prior advance of ≥ 20% in the 60 bars before base
    - 15-50 candle consolidation with range < 15%
    - Volume contracting in second half of base vs first half
    - Current price near base high (within 5%)
    """
    NO_PATTERN = {"detected": False, "base_depth_pct": None, "resistance_level": None,
                  "breakout_detected": False, "breakout_level": None, "base_length": None}

    data = df.tail(120).reset_index(drop=True)
    n = len(data)
    if n < 30:
        return NO_PATTERN

    closes = data["Close"].values
    highs = data["High"].values
    lows = data["Low"].values
    volumes = data["Volume"].values

    for base_len in range(15, 51):
        if base_len > n - 15:
            break

        base_start = n - base_len
        b_highs = highs[base_start:]
        b_lows = lows[base_start:]
        b_vols = volumes[base_start:]

        b_high = float(b_highs.max())
        b_low = float(b_lows.min())
        if b_high <= 0:
            continue

        depth = (b_high - b_low) / b_high
        if depth > 0.15:
            continue

        # Prior advance ≥ 20% in 60 bars before base
        lookback_start = max(0, base_start - 60)
        prior_close = closes[lookback_start]
        base_entry_close = closes[base_start]
        if prior_close <= 0 or base_entry_close < prior_close * 1.20:
            continue

        # Volume contraction: second half of base should not be expanding
        half = base_len // 2
        vol_first = float(b_vols[:half].mean())
        vol_second = float(b_vols[half:].mean())
        if vol_first > 0 and vol_second >= vol_first * 1.15:
            continue

        # Current price near the base high (within 5%)
        current_price = float(closes[-1])
        if current_price < b_high * 0.95:
            continue

        pivot = b_high
        breakout = current_price >= pivot * 0.995

        return {
            "detected": True,
            "base_depth_pct": round(depth * 100, 2),
            "resistance_level": round(pivot, 2),
            "breakout_detected": breakout,
            "breakout_level": round(pivot, 2),
            "base_length": base_len,
        }

    return NO_PATTERN


def detect_double_bottom(df: pd.DataFrame) -> dict:
    """
    Double Bottom (W-shape) with optional Handle:
    - Two swing lows within 5% of each other, second ≥ first (0.98x)
    - Separated by at least 10 bars
    - Middle peak between lows at least 10% above the bottoms
    - Right-side recovery to ≥ 90% of middle peak
    - Optional handle after right-side high: depth ≤ 10%
    - Pivot = middle peak (buy on breakout above it)
    """
    NO_PATTERN = {"detected": False, "bottom_depth_pct": None, "bottom_diff_pct": None,
                  "resistance_level": None, "breakout_detected": False, "breakout_level": None}

    data = df.tail(150).reset_index(drop=True)
    n = len(data)
    if n < 40:
        return NO_PATTERN

    closes = data["Close"].values
    highs = data["High"].values
    lows = data["Low"].values

    swing_low_idxs = find_swing_lows(pd.Series(lows), window=7)
    if len(swing_low_idxs) < 2:
        return NO_PATTERN

    for i in range(len(swing_low_idxs) - 1, 0, -1):
        lo2_idx = swing_low_idxs[i]
        lo1_idx = swing_low_idxs[i - 1]

        lo1 = lows[lo1_idx]
        lo2 = lows[lo2_idx]

        if lo1 <= 0:
            continue

        # Two bottoms within 5% of each other
        bottom_diff = abs(lo1 - lo2) / lo1
        if bottom_diff > 0.05:
            continue

        # Second bottom must not be significantly lower than first
        if lo2 < lo1 * 0.98:
            continue

        # Bottoms must be separated by at least 10 bars
        if lo2_idx - lo1_idx < 10:
            continue

        # Middle peak between the two lows
        mid_highs = highs[lo1_idx: lo2_idx + 1]
        mid_high = float(mid_highs.max())

        # Recovery between bottoms ≥ 10% above first bottom
        if lo1 > 0 and (mid_high - lo1) / lo1 < 0.10:
            continue

        # Right side: recovery after lo2 must reach ≥ 90% of mid peak
        right_region = highs[lo2_idx:]
        if len(right_region) < 5:
            continue

        right_high = float(right_region.max())
        right_high_local_idx = lo2_idx + int(np.argmax(right_region))

        if right_high < mid_high * 0.90:
            continue

        # Optional handle after right-side high
        handle_start = right_high_local_idx + 1
        if handle_start < n and (n - handle_start) >= 3:
            handle_low = float(lows[handle_start:].min())
            handle_depth = (right_high - handle_low) / right_high if right_high > 0 else 0
            if handle_depth > 0.10:
                continue

        pivot = mid_high
        current_price = float(closes[-1])
        breakout = current_price >= pivot * 0.995
        bottom_depth = (mid_high - min(lo1, lo2)) / mid_high if mid_high > 0 else 0

        return {
            "detected": True,
            "bottom_depth_pct": round(bottom_depth * 100, 2),
            "bottom_diff_pct": round(bottom_diff * 100, 2),
            "resistance_level": round(pivot, 2),
            "breakout_detected": breakout,
            "breakout_level": round(pivot, 2),
        }

    return NO_PATTERN


def detect_ascending_triangle(df: pd.DataFrame) -> dict:
    """
    Ascending Triangle:
    - At least 3 swing highs clustered within 4% (flat resistance line)
    - At least 3 swing lows each ≥ 0.5% higher than previous (ascending support)
    - Volume contracting (second half of window < first half)
    - Current price within 5% of resistance
    """
    NO_PATTERN = {"detected": False, "resistance_level": None,
                  "breakout_detected": False, "breakout_level": None}

    data = df.tail(80).reset_index(drop=True)
    n = len(data)
    if n < 30:
        return NO_PATTERN

    closes = data["Close"].values
    highs = data["High"].values
    lows = data["Low"].values
    volumes = data["Volume"].values

    swing_high_idxs = find_swing_highs(pd.Series(highs), window=5)
    swing_low_idxs = find_swing_lows(pd.Series(lows), window=5)

    if len(swing_high_idxs) < 3 or len(swing_low_idxs) < 3:
        return NO_PATTERN

    sh_idxs = swing_high_idxs[-5:]
    sl_idxs = swing_low_idxs[-5:]

    # Flat resistance: all swing highs within 4% band
    sh_prices = [highs[i] for i in sh_idxs]
    sh_max = max(sh_prices)
    sh_min = min(sh_prices)
    if sh_max <= 0 or (sh_max - sh_min) / sh_max > 0.04:
        return NO_PATTERN

    resistance = sh_max

    # Ascending lows: each subsequent low at least 0.5% higher
    sl_prices = [lows[i] for i in sl_idxs]
    ascending = all(sl_prices[j + 1] >= sl_prices[j] * 1.005 for j in range(len(sl_prices) - 1))
    if not ascending:
        return NO_PATTERN

    # Volume contracting
    mid = n // 2
    early_vol = float(volumes[:mid].mean())
    late_vol = float(volumes[mid:].mean())
    if early_vol > 0 and late_vol >= early_vol:
        return NO_PATTERN

    # Price approaching resistance (within 5%)
    current_price = float(closes[-1])
    if current_price < resistance * 0.95:
        return NO_PATTERN

    breakout = current_price >= resistance * 0.995

    return {
        "detected": True,
        "resistance_level": round(resistance, 2),
        "breakout_detected": breakout,
        "breakout_level": round(resistance, 2),
    }


def detect_base_on_base(df: pd.DataFrame) -> dict:
    """
    Base-on-Base:
    - Two consecutive tight consolidations stacked at higher price levels
    - Each base: 15-50 bars, range < 15%
    - Second base's low is above first base's low, and starts near first base's high (within 20%)
    """
    NO_PATTERN = {"detected": False, "first_base_top": None, "second_base_top": None,
                  "resistance_level": None, "breakout_detected": False, "breakout_level": None}

    data = df.tail(150).reset_index(drop=True)
    n = len(data)
    if n < 50:
        return NO_PATTERN

    closes = data["Close"].values
    highs = data["High"].values
    lows = data["Low"].values

    # Base 2: currently forming (last 15-50 bars)
    base2 = None
    for base2_len in range(15, 51):
        if base2_len > n - 20:
            break
        b2_start = n - base2_len
        b2_high = float(highs[b2_start:].max())
        b2_low = float(lows[b2_start:].min())
        if b2_high <= 0:
            continue
        if (b2_high - b2_low) / b2_high <= 0.15:
            base2 = {"start": b2_start, "high": b2_high, "low": b2_low}
            break

    if base2 is None:
        return NO_PATTERN

    # Base 1: in the 15-50 bars immediately before Base 2
    base1 = None
    for base1_len in range(15, 51):
        b1_end = base2["start"]
        b1_start = b1_end - base1_len
        if b1_start < 0:
            break
        b1_high = float(highs[b1_start: b1_end].max())
        b1_low = float(lows[b1_start: b1_end].min())
        if b1_high <= 0:
            continue
        if (b1_high - b1_low) / b1_high <= 0.15:
            base1 = {"start": b1_start, "end": b1_end, "high": b1_high, "low": b1_low}
            break

    if base1 is None:
        return NO_PATTERN

    # Base 2 must sit at a higher price level
    if base2["low"] <= base1["low"]:
        return NO_PATTERN

    # Base 2 starts close to Base 1's high (stacked, not far away)
    if base2["low"] > base1["high"] * 1.20:
        return NO_PATTERN

    pivot = base2["high"]
    current_price = float(closes[-1])
    breakout = current_price >= pivot * 0.995

    return {
        "detected": True,
        "first_base_top": round(base1["high"], 2),
        "second_base_top": round(base2["high"], 2),
        "resistance_level": round(pivot, 2),
        "breakout_detected": breakout,
        "breakout_level": round(pivot, 2),
    }


def detect_high_tight_flag(df: pd.DataFrame) -> dict:
    """
    High Tight Flag:
    - Pole: ≥ 90% gain in 10-40 bars (explosive momentum)
    - Flag: 10-25% pullback in ≤ 20 bars after pole
    - Volume drops ≥ 30% in flag vs pole
    - Pivot = pole high (buy on breakout above it)
    """
    NO_PATTERN = {"detected": False, "pole_gain_pct": None, "flag_depth_pct": None,
                  "resistance_level": None, "breakout_detected": False, "breakout_level": None}

    data = df.tail(80).reset_index(drop=True)
    n = len(data)
    if n < 25:
        return NO_PATTERN

    closes = data["Close"].values
    highs = data["High"].values
    lows = data["Low"].values
    volumes = data["Volume"].values

    # Find most recent pole: ≥ 90% gain in 10-40 bars
    pole_end = None
    pole_start = None
    pole_gain = 0.0

    for end in range(n - 1, 14, -1):
        for window in range(10, 41):
            start = end - window
            if start < 0:
                continue
            if closes[start] <= 0:
                continue
            gain = (closes[end] - closes[start]) / closes[start]
            if gain >= 0.90:
                pole_end = end
                pole_start = start
                pole_gain = gain
                break
        if pole_end is not None:
            break

    if pole_end is None or pole_end >= n - 3:
        return NO_PATTERN

    flag_start = pole_end + 1
    flag_lows = lows[flag_start:]
    flag_vols = volumes[flag_start:]
    flag_len = n - flag_start

    if not (3 <= flag_len <= 20):
        return NO_PATTERN

    pole_high_price = float(highs[pole_end])
    if pole_high_price <= 0:
        return NO_PATTERN

    flag_low = float(flag_lows.min())
    flag_depth = (pole_high_price - flag_low) / pole_high_price

    if not (0.10 <= flag_depth <= 0.25):
        return NO_PATTERN

    # Volume must drop ≥ 30% in flag vs pole
    pole_avg_vol = float(volumes[pole_start: pole_end + 1].mean())
    flag_avg_vol = float(flag_vols.mean()) if len(flag_vols) > 0 else 0.0
    if pole_avg_vol > 0 and flag_avg_vol >= pole_avg_vol * 0.70:
        return NO_PATTERN

    pivot = pole_high_price
    current_price = float(closes[-1])
    breakout = current_price >= pivot * 0.995

    return {
        "detected": True,
        "pole_gain_pct": round(pole_gain * 100, 2),
        "flag_depth_pct": round(flag_depth * 100, 2),
        "resistance_level": round(pivot, 2),
        "breakout_detected": breakout,
        "breakout_level": round(pivot, 2),
    }
