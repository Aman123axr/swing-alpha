# Swing Alpha — Architecture

## System Overview

```
Browser (Next.js 14)
    │
    │  /api/scan (same-origin proxy)
    ▼
Next.js Server (Route Handlers)
    │
    │  HTTP POST to FASTAPI_URL
    ▼
FastAPI (Python)
    │
    ├── data_fetcher.py ──► yfinance (Yahoo Finance)
    ├── indicators.py   ──► EMA, swing point computation
    ├── pattern_detector.py ──► VCP, Bull Flag detection
    └── scorer.py       ──► Scoring rules + Entry/SL
```

---

## Component Responsibilities

### Backend (`backend/`)

| File | Responsibility |
|---|---|
| `main.py` | FastAPI app, CORS, in-memory cache (15 min TTL), request routing |
| `data_fetcher.py` | yfinance wrapper, ticker normalization, fundamentals extraction |
| `indicators.py` | EMA computation, swing high/low detection (pure functions) |
| `pattern_detector.py` | VCP and Bull Flag detection algorithms (pure functions, no side effects) |
| `scorer.py` | Aggregates scores, computes entry/SL, assembles final result dict |

### Frontend (`frontend/`)

| File | Responsibility |
|---|---|
| `app/page.tsx` | Dashboard root — state management, scan trigger, watchlist (localStorage) |
| `app/api/*/route.ts` | Server-side proxy routes — forward browser requests to FastAPI, keep FastAPI URL server-side |
| `components/StockTable.tsx` | Sortable, filterable results table with score columns |
| `components/TopStocks.tsx` | Top-5 highlight cards |
| `components/FilterBar.tsx` | "High Conviction only" toggle, sort, search |
| `components/UploadCSV.tsx` | CSV drag-and-drop, auto-detects ticker column |
| `lib/types.ts` | TypeScript interfaces shared across components |

---

## Data Flow

```
1. User opens dashboard
   → page.tsx mounts, loads watchlist from localStorage
   → calls triggerScan() with DEFAULT_TICKERS

2. triggerScan()
   → POST /api/scan (Next.js route handler)
   → Route handler POSTs to FastAPI /api/scan
   → FastAPI: normalize tickers → fetch OHLCV + fundamentals via yfinance
   → compute EMAs → detect VCP + Bull Flag → score → sort → return

3. Results arrive
   → page.tsx sets scanResults state
   → StockTable renders sorted results
   → TopStocks renders top 5 cards

4. CSV upload
   → UploadCSV sends file to /api/upload-csv
   → FastAPI parses CSV, returns ticker list
   → page.tsx updates tickerList → re-triggers scan

5. Watchlist
   → Star click in StockTable toggles ticker in watchlist array
   → page.tsx persists watchlist to localStorage on every change
```

---

## Key Design Decisions

1. **Next.js proxies all API calls** — avoids browser CORS issues; FastAPI URL stays server-side only
2. **In-memory cache (15 min)** — prevents re-fetching the same ticker on UI refresh; no database needed
3. **asyncio.Semaphore(5)** — allows up to 5 concurrent yfinance requests; prevents rate limiting
4. **Pattern detection on last 60 candles** — enough to detect 3+ contractions without noise from older data
5. **period="1y" for OHLCV** — provides ~252 trading days, needed for EMA-200 to stabilize
6. **No database** — all state is either in-memory (backend) or localStorage (frontend); simplifies deployment

---

## Running Locally

See `README.md` for full setup instructions.

Ports:
- Backend (FastAPI): `http://localhost:8000`
- Frontend (Next.js): `http://localhost:3000`
