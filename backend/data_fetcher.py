import datetime
import yfinance as yf
import pandas as pd
from typing import Optional


def _drop_todays_partial_bar(df: pd.DataFrame) -> pd.DataFrame:
    """Remove today's bar so scores are based only on complete EOD sessions."""
    if df.empty or len(df) < 2:
        return df
    last_date = pd.Timestamp(df.index[-1]).date()
    if last_date == datetime.date.today():
        return df.iloc[:-1]
    return df


def normalize_ticker(ticker: str) -> str:
    ticker = ticker.strip().upper()
    if "." not in ticker:
        return ticker + ".NS"
    return ticker


def fetch_ohlcv(ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period=period, interval="1d", auto_adjust=True)
        if df.empty or len(df) < 30:
            return None
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.dropna(inplace=True)
        return _drop_todays_partial_bar(df)
    except Exception:
        return None


def fetch_ohlcv_batch(tickers: list, period: str = "1y") -> dict:
    """Download OHLCV for many tickers. Tries batch first, falls back to individual calls."""
    result = {}

    # --- batch attempt (fastest when it works) ---
    try:
        raw = yf.download(
            tickers,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=False,      # more stable in containerised envs
        )
        if not raw.empty:
            if len(tickers) == 1:
                df = raw[["Open", "High", "Low", "Close", "Volume"]].dropna()
                df = _drop_todays_partial_bar(df)
                if len(df) >= 30:
                    result[tickers[0]] = df
            else:
                for ticker in tickers:
                    try:
                        df = raw[ticker][["Open", "High", "Low", "Close", "Volume"]].dropna()
                        df = _drop_todays_partial_bar(df)
                        if len(df) >= 30:
                            result[ticker] = df
                    except Exception:
                        pass
    except Exception:
        pass

    # --- individual fallback for any ticker the batch missed ---
    missing = [t for t in tickers if t not in result]
    for ticker in missing:
        df = fetch_ohlcv(ticker, period)
        if df is not None:
            result[ticker] = df

    return result


def fetch_fundamentals(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        return {
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            # yfinance returns this as a percentage value (e.g. 45.2 = D/E ratio 0.452)
            "debt_to_equity": info.get("debtToEquity"),
            "held_percent_institutions": info.get("heldPercentInstitutions"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "day_change_pct": info.get("regularMarketChangePercent"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "short_name": info.get("shortName") or info.get("longName") or ticker,
            "market_cap": info.get("marketCap"),
        }
    except Exception:
        return {}
