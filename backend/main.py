import asyncio
import io
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import List, Optional

import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chartink_fetcher import get_tickers_from_screener
from data_fetcher import normalize_ticker, fetch_ohlcv, fetch_ohlcv_batch, fetch_fundamentals
from scorer import score_stock
from backtester import backtest_ticker, _compute_stats

logger = logging.getLogger(__name__)

# In-memory store for last ChartInk fetch
CHARTINK_LATEST: dict = {
    "tickers": [],
    "fetched_at": None,
    "count": 0,
}

scheduler = AsyncIOScheduler()


async def _run_chartink_fetch():
    loop = asyncio.get_event_loop()
    try:
        logger.info("ChartInk scheduled fetch starting…")
        tickers = await loop.run_in_executor(None, get_tickers_from_screener)
        CHARTINK_LATEST["tickers"] = tickers
        CHARTINK_LATEST["fetched_at"] = time.time()
        CHARTINK_LATEST["count"] = len(tickers)
        logger.info("ChartInk fetch complete: %d tickers", len(tickers))
    except Exception as e:
        logger.error("ChartInk fetch failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 3:45 PM IST = 10:15 AM UTC, weekdays only
    scheduler.add_job(
        _run_chartink_fetch,
        trigger="cron",
        day_of_week="mon-fri",
        hour=10,
        minute=15,
        timezone="UTC",
        id="chartink_daily",
        replace_existing=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Swing Alpha API", version="1.0.0", lifespan=lifespan)

_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000")
_cors_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# In-memory cache: ticker -> {result: dict, fetched_at: float}
SCAN_CACHE: dict = {}
CACHE_TTL_SECONDS = 900  # 15 minutes

DEFAULT_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "BAJFINANCE.NS", "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS",
    "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS", "SUNPHARMA.NS", "WIPRO.NS",
    "ULTRACEMCO.NS", "NESTLEIND.NS", "TECHM.NS", "POWERGRID.NS", "NTPC.NS",
]


class ScanRequest(BaseModel):
    tickers: List[str]


class BacktestRequest(BaseModel):
    tickers: List[str]
    rr_ratio: float = 2.0
    max_hold_days: int = 20
    max_loss_pct: float = 5.0
    max_profit_pct: float = 15.0
    breakout_only: bool = False


def _is_cache_valid(ticker: str) -> bool:
    entry = SCAN_CACHE.get(ticker)
    if not entry:
        return False
    return (time.time() - entry["fetched_at"]) < CACHE_TTL_SECONDS


async def _fetch_fundamentals_one(ticker: str, semaphore: asyncio.Semaphore) -> tuple:
    async with semaphore:
        loop = asyncio.get_event_loop()
        try:
            fund = await loop.run_in_executor(None, fetch_fundamentals, ticker)
            return ticker, fund
        except Exception:
            return ticker, {}


@app.get("/")
def root():
    return {"message": "Swing Alpha API", "docs": "/docs"}


@app.get("/api/chartink/latest")
def chartink_latest():
    if not CHARTINK_LATEST["fetched_at"]:
        return {"tickers": [], "count": 0, "fetched_at": None}
    return CHARTINK_LATEST


@app.post("/api/chartink/fetch")
async def chartink_fetch():
    """Manually trigger a ChartInk 52-week-high screener fetch."""
    await _run_chartink_fetch()
    if not CHARTINK_LATEST["tickers"]:
        raise HTTPException(status_code=502, detail="ChartInk fetch returned no data")
    return CHARTINK_LATEST


@app.get("/api/defaults")
def get_defaults():
    return {"tickers": DEFAULT_TICKERS}


@app.post("/api/scan")
async def scan_stocks(payload: ScanRequest):
    tickers = [normalize_ticker(t) for t in payload.tickers if t.strip()]
    if not tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")

    cached_results = []
    uncached = []
    for ticker in tickers:
        if _is_cache_valid(ticker):
            cached_results.append(SCAN_CACHE[ticker]["result"])
        else:
            uncached.append(ticker)

    fresh_results = []
    if uncached:
        loop = asyncio.get_event_loop()

        # One batch call for all OHLCV — much faster than individual calls
        ohlcv_map = await loop.run_in_executor(None, fetch_ohlcv_batch, uncached)

        # Fetch fundamentals in parallel (includes day_change_pct from Yahoo Finance)
        sem = asyncio.Semaphore(10)
        fund_pairs = await asyncio.gather(
            *[_fetch_fundamentals_one(t, sem) for t in uncached]
        )
        fund_map = dict(fund_pairs)

        for ticker in uncached:
            df = ohlcv_map.get(ticker)
            if df is None or df.empty:
                continue
            try:
                result = score_stock(ticker, df, fund_map.get(ticker, {}))
                SCAN_CACHE[ticker] = {"result": result, "fetched_at": time.time()}
                fresh_results.append(result)
            except Exception as e:
                print(f"Score error {ticker}: {e}")

    all_results = cached_results + fresh_results
    all_results.sort(key=lambda x: x["total_score"], reverse=True)
    return {"results": all_results, "scanned": len(tickers), "returned": len(all_results)}


@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to parse CSV")

    # Find ticker column (case-insensitive match for ticker/symbol/stock)
    col = None
    for c in df.columns:
        if c.strip().lower() in ("ticker", "symbol", "stock", "scrip"):
            col = c
            break
    if col is None:
        col = df.columns[0]  # fallback: first column

    tickers_raw = df[col].dropna().astype(str).str.strip().tolist()
    tickers = [normalize_ticker(t) for t in tickers_raw if t]
    if not tickers:
        raise HTTPException(status_code=400, detail="No valid tickers found in CSV")

    return {"tickers": tickers, "count": len(tickers)}


@app.post("/api/backtest")
async def backtest_stocks(payload: BacktestRequest):
    tickers = [normalize_ticker(t) for t in payload.tickers if t.strip()]
    if not tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")
    if len(tickers) > 200:
        raise HTTPException(status_code=400, detail="Maximum 200 tickers per backtest")

    loop = asyncio.get_event_loop()
    semaphore = asyncio.Semaphore(3)

    async def run_one(ticker: str):
        async with semaphore:
            try:
                df = await loop.run_in_executor(None, fetch_ohlcv, ticker)
                if df is None or len(df) < 90:
                    return None
                return await loop.run_in_executor(
                    None, backtest_ticker, ticker, df,
                    payload.rr_ratio, payload.max_hold_days,
                    payload.max_loss_pct, payload.max_profit_pct,
                    payload.breakout_only,
                )
            except Exception as e:
                print(f"Backtest error {ticker}: {e}")
                return None

    raw = await asyncio.gather(*[run_one(t) for t in tickers])
    results = [r for r in raw if r is not None]

    all_trades = [
        {**trade, "ticker": r["ticker"]}
        for r in results
        for trade in r["trades"]
    ]
    all_trades_sorted = sorted(all_trades, key=lambda t: t["signal_date"])

    return {
        "results": results,
        "aggregate": _compute_stats(all_trades_sorted),
        "total_tickers": len(results),
        "all_trades": all_trades_sorted,
    }


@app.get("/api/stock/{ticker}")
async def get_stock_detail(ticker: str):
    normalized = normalize_ticker(ticker)
    if _is_cache_valid(normalized):
        return SCAN_CACHE[normalized]["result"]

    semaphore = asyncio.Semaphore(1)
    result = await _analyse_ticker(normalized, semaphore)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}")

    SCAN_CACHE[normalized] = {"result": result, "fetched_at": time.time()}
    return result
