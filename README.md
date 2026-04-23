# Swing Alpha

Rule-based swing trading stock scanner for Indian equity markets (NSE/BSE).

Detects **VCP** (Volatility Contraction Pattern) and **Bullish Flag** patterns using strict, deterministic rules on OHLCV data. Scores each stock out of 10 across trend, pattern, volume, and fundamentals. No AI, no ML, no guessing.

---

## How to Run Locally

### Prerequisites

- Python 3.11+
- Node.js 20+ / npm

---

### 1. Backend (FastAPI)

```bash
cd "Swing Alpha/backend"

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

Verify: open http://localhost:8000/docs — Swagger UI should show all endpoints.

---

### 2. Frontend (Next.js)

```bash
cd "Swing Alpha/frontend"

npm install
npm run dev
```

Open http://localhost:3000

---

### 3. First Run

1. The dashboard auto-scans 20 Nifty50 stocks on load
2. Wait ~30–60 seconds for all data to fetch
3. Results appear sorted by score with color-coded categories

---

## Pattern Detection — How It Works

### VCP (Volatility Contraction Pattern)

Works on the last 60 candles:

1. Find swing highs and lows (local extremes within ±5 candle window)
2. Pair each swing high with the next swing low → one "contraction segment"
3. Compute `range_pct = (high − low) / high` per segment
4. Require ≥3 contractions with each range smaller than the previous
5. Volume must decline: final contraction avg vol < first × 0.8
6. Resistance proximity: latest high must be within 8% of the 60-candle high
7. Tightness: final contraction range < 8%
8. Breakout: price within 0.5% of resistance

### Bull Flag

1. Find flagpole: window of 5–15 candles with ≥8% cumulative gain
2. All candles after flagpole top = consolidation
3. Consolidation avg volume < flagpole avg volume
4. At most 1 close below 20 EMA during consolidation
5. Linear regression slope ≤ +0.3%/candle (flat or slightly down)
6. Retracement from pole high ≤ 50%
7. Breakout: price ≥ consolidation high × 0.995

---

## Scoring — Step-by-Step Example

**Stock: TITAN.NS (hypothetical values)**

| Component | Condition | Score |
|---|---|---|
| Trend | 20EMA > 44EMA > 200EMA, price above all | 3/3 |
| Pattern | VCP detected (3 contractions, tight) | 2/2 |
| Volume | Last volume = 1.7× 20-day avg | 2/2 |
| Growth | Rev +18%, Earn +22% (both ≥15%) | 1.5 |
| Debt | D/E ratio = 0.12 (< 0.5) | 1.0 |
| Institutional | 14% institutional holding | 0.5 |
| **Total** | | **10/10 — High Conviction** |

---

## Features

| Feature | Details |
|---|---|
| Pattern detection | VCP, Bull Flag (strict rule-based) |
| Scoring | 10-point system, 4 components |
| Default list | 20 Nifty50 stocks |
| CSV upload | Drag-and-drop, auto-detects ticker column |
| Watchlist | Persisted in localStorage |
| Filter | High Conviction only toggle |
| Sort | By any score column |
| Cache | 15-minute server-side cache (prevents rate limiting) |

---

## CSV Format

Upload a `.csv` file with a column named `ticker`, `symbol`, `stock`, or `scrip`:

```
ticker
RELIANCE.NS
TCS.NS
INFY
```

If no `.NS`/`.BO` suffix is present, `.NS` is auto-appended.

---

## Documentation

- [SPEC.md](SPEC.md) — Full system specification and scoring rules
- [API.md](API.md) — Backend API reference
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and data flow
