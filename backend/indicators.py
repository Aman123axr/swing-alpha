import pandas as pd
import numpy as np
from typing import List


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def add_emas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ema_20"] = compute_ema(df["Close"], 20)
    df["ema_44"] = compute_ema(df["Close"], 44)
    df["ema_200"] = compute_ema(df["Close"], 200)
    return df


def compute_avg_volume(df: pd.DataFrame, lookback: int = 20) -> float:
    return float(df["Volume"].iloc[-lookback:].mean())


def find_swing_highs(series: pd.Series, window: int = 5) -> List[int]:
    highs = []
    vals = series.values
    n = len(vals)
    for i in range(window, n - window):
        neighborhood = vals[i - window: i + window + 1]
        if vals[i] == neighborhood.max():
            highs.append(i)
    return highs


def find_swing_lows(series: pd.Series, window: int = 5) -> List[int]:
    lows = []
    vals = series.values
    n = len(vals)
    for i in range(window, n - window):
        neighborhood = vals[i - window: i + window + 1]
        if vals[i] == neighborhood.min():
            lows.append(i)
    return lows
