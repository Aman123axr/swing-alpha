# Swing Alpha — API Reference

Base URL (local): `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

## GET /

Health check.

**Response:**
```json
{ "message": "Swing Alpha API", "docs": "/docs" }
```

---

## GET /api/defaults

Returns the default list of 20 Nifty50 tickers used when no CSV is uploaded.

**Response:**
```json
{
  "tickers": ["RELIANCE.NS", "TCS.NS", ...]
}
```

---

## POST /api/scan

Run a full analysis (pattern detection + scoring) on a list of tickers.  
Results are cached for 15 minutes per ticker.

**Request body:**
```json
{ "tickers": ["RELIANCE.NS", "TCS.NS"] }
```

**Response:**
```json
{
  "results": [ <StockResult>, ... ],
  "scanned": 2,
  "returned": 2
}
```

**StockResult schema:**
```json
{
  "ticker": "RELIANCE.NS",
  "short_name": "Reliance Industries Ltd",
  "current_price": 2850.0,
  "total_score": 7.5,
  "trend_score": 3,
  "pattern_score": 2,
  "volume_score": 1,
  "fund_score": 1.5,
  "pattern_type": "VCP",
  "category": "Good Swing",
  "entry": 2870.0,
  "stop_loss": 2740.0,
  "ema_20": 2810.0,
  "ema_44": 2770.0,
  "ema_200": 2600.0,
  "revenue_growth_pct": 12.0,
  "earnings_growth_pct": 9.5,
  "debt_to_equity": 0.35,
  "institutional_holding_pct": 18.2,
  "fifty_two_week_high": 3025.0,
  "vcp": {
    "detected": true,
    "contraction_count": 3,
    "resistance_level": 2875.0,
    "breakout_detected": false,
    "breakout_level": 2875.0,
    "last_range_pct": 4.2
  },
  "bull_flag": {
    "detected": false,
    ...
  }
}
```

---

## POST /api/upload-csv

Upload a CSV file containing a list of tickers to scan.

**Request:** `multipart/form-data`, field name `file`, `.csv` extension required.

**CSV format:**  
Column header should be one of: `ticker`, `symbol`, `stock`, `scrip` (case-insensitive).  
If none found, the first column is used.

**Example CSV:**
```
ticker
RELIANCE.NS
TCS.NS
INFY
```

**Response:**
```json
{ "tickers": ["RELIANCE.NS", "TCS.NS", "INFY.NS"], "count": 3 }
```

---

## GET /api/stock/{ticker}

Fetch full analysis for a single stock. Uses cache if available.

**Example:** `GET /api/stock/TCS.NS`

**Response:** Single `StockResult` object (same schema as above).

---

## Error Responses

| Code | Reason |
|---|---|
| 400 | No tickers provided / invalid CSV / non-CSV file |
| 404 | Stock data unavailable (no OHLCV returned from yfinance) |
| 500 | Unexpected server error |
