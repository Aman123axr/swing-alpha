# Swing Alpha — System Specification

## 1. Purpose

A rule-based swing trading stock selection system for Indian equity markets (NSE/BSE).  
**No AI, no ML, no averaging, no subjective scoring** — every decision is deterministic and verifiable.

---

## 2. Input Sources

| Source | Method |
|---|---|
| Default 20 Nifty50 stocks | Hardcoded list in backend |
| CSV upload | Column header: `ticker`, `symbol`, `stock`, or `scrip` |
| Yahoo Finance (yfinance) | Primary data API |

Ticker format: Yahoo Finance requires `.NS` suffix for NSE (e.g. `RELIANCE.NS`).  
Auto-normalization: if no `.` in ticker string, append `.NS`.

---

## 3. Data Requirements Per Stock

### Technical (from yfinance OHLCV history, `period="1y"`, `interval="1d"`)
- Open, High, Low, Close, Volume — last ~252 trading days
- 20 EMA, 44 EMA, 200 EMA (computed from Close via exponential weighted mean)
- 20-day average volume

### Fundamental (from `yf.Ticker().info`)
- `revenueGrowth` — YoY revenue growth (decimal, e.g. 0.18 = 18%)
- `earningsGrowth` — YoY earnings/EPS growth (decimal)
- `debtToEquity` — **stored as a percentage** in yfinance (e.g. 45.2 = D/E ratio 0.452); divide by 100 before use
- `heldPercentInstitutions` — 0 to 1 float
- `currentPrice` / `regularMarketPrice` — last traded price
- `fiftyTwoWeekHigh`

Missing fields default to `0` (not an error).

---

## 4. Scoring System (Total = 10)

### 4.1 Trend Structure (0–3)

```
IF 20EMA > 44EMA > 200EMA AND price > 20EMA → 3
ELSE IF 20EMA > 200EMA OR price > 44EMA     → 2
ELSE                                         → 0
```

### 4.2 Price Action / Pattern (0–2)

VCP or Bull Flag detected → 2  
Price above 20 EMA (loose structure) → 1  
None → 0

See §5 for detection algorithms.

### 4.3 Volume Confirmation (0–2)

```
last_volume / 20d_avg_volume:
  ≥ 1.5 → 2
  ≥ 1.0 → 1
  < 1.0 → 0
```

### 4.4 Fundamentals (0–3)

| Component | Condition | Score |
|---|---|---|
| Growth | `rev_growth ≥ 15% AND earn_growth ≥ 15%` | 1.5 |
| Growth | `rev_growth ≥ 8% OR earn_growth ≥ 8%` | 1.0 |
| Growth | Neither | 0 |
| Debt | `D/E ratio < 0.5` | 1.0 |
| Institutional | `inst_holding > 1%` | 0.5 |

Max fundamentals score = 3.0

### 4.5 Classification

| Score | Category |
|---|---|
| ≥ 8.0 | High Conviction |
| 6.0 – 7.9 | Good Swing |
| < 6.0 | Avoid |

---

## 5. Pattern Detection Algorithms

### 5.1 VCP (Volatility Contraction Pattern)

**Window:** Last 60 candles

**Algorithm:**
1. Find swing highs using local maximum within ±5 candle window
2. Find swing lows using local minimum within ±5 candle window
3. Build contraction segments: pair each swing high with the next swing low after it
4. Compute `range_pct = (high_price − low_price) / high_price` per segment
5. Count consecutive range shrinks; require `shrink_count ≥ 2` (= 3+ contractions)
6. Volume check: `avg_vol[last_contraction] < avg_vol[first_contraction] × 0.8`
7. Resistance proximity: `last_contraction.high_price / resistance_60d ≥ 0.92` (within 8%)
8. Tightness: `last_contraction.range_pct < 0.08` (< 8% range)
9. Breakout flag: `current_price ≥ resistance × 0.995`

**Output:** `{detected, contraction_count, resistance_level, breakout_detected, breakout_level, last_range_pct}`

### 5.2 Bullish Flag

**Algorithm:**
1. Scan from most recent candle backward in windows 5–15 candles; find first with `gain ≥ 8%` = flagpole
2. All candles after flagpole top = consolidation
3. Volume: `avg_consol_vol < avg_pole_vol` (must drop)
4. EMA support: at most 1 close below 20 EMA during consolidation
5. Channel slope: linear regression slope ≤ `+0.3%` per candle (flat or down)
6. Depth: `(pole_high − consol_low) / pole_high ≤ 0.50` (max 50% retracement)
7. Breakout: `current_price ≥ consol_high × 0.995`

**Output:** `{detected, pole_gain_pct, consol_depth_pct, resistance_level, breakout_detected, breakout_level}`

---

## 6. Entry and Stop Loss Logic

```
Entry:
  IF breakout detected (VCP or Flag) → breakout_level
  ELSE IF VCP detected               → resistance_level (buy near resistance)
  ELSE IF Flag detected              → resistance_level
  ELSE                               → current_price

Stop Loss:
  sl_ema   = ema_20 × 0.99           (1% below 20 EMA)
  sl_swing = last_swing_low × 0.995  (0.5% below last swing low)
  SL       = max(sl_ema, sl_swing)   (tighter = higher value)
```

---

## 7. Strict Rules (Non-Negotiable)

- No averaging of scores across any criteria
- No machine learning or probabilistic inference
- No subjective scoring — each criterion has exact numeric thresholds
- Pattern detection operates only on OHLCV candle data
- Missing data → default to 0 (neutral), never interpolate or estimate

---

## 8. Default Ticker List

20 Nifty50 stocks (NSE):  
`RELIANCE`, `TCS`, `INFY`, `HDFCBANK`, `ICICIBANK`, `HINDUNILVR`, `BAJFINANCE`,  
`KOTAKBANK`, `LT`, `AXISBANK`, `ASIANPAINT`, `MARUTI`, `TITAN`, `SUNPHARMA`,  
`WIPRO`, `ULTRACEMCO`, `NESTLEIND`, `TECHM`, `POWERGRID`, `NTPC`
