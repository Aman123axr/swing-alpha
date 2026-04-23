export interface VCPResult {
  detected: boolean
  contraction_count: number
  resistance_level: number | null
  breakout_detected: boolean
  breakout_level: number | null
  last_range_pct: number | null
}

export interface BullFlagResult {
  detected: boolean
  pole_gain_pct: number | null
  consol_depth_pct: number | null
  resistance_level: number | null
  breakout_detected: boolean
  breakout_level: number | null
}

export type PatternType = "VCP" | "Bull Flag" | "Loose Structure" | "None"
export type Category = "High Conviction" | "Good Swing" | "Avoid"
export type SortKey =
  | "total_score"
  | "trend_score"
  | "pattern_score"
  | "volume_score"
  | "fund_score"
  | "current_price"
  | "day_change_pct"

export interface StockResult {
  ticker: string
  short_name: string
  current_price: number | null
  day_change_pct: number | null
  total_score: number
  trend_score: number
  pattern_score: number
  volume_score: number
  fund_score: number
  pattern_type: PatternType
  category: Category
  entry: number
  stop_loss: number
  ema_20: number
  ema_44: number
  ema_200: number
  revenue_growth_pct: number
  earnings_growth_pct: number
  debt_to_equity: number | null
  institutional_holding_pct: number
  fifty_two_week_high: number | null
  vcp: VCPResult
  bull_flag: BullFlagResult
}

export interface ScanResponse {
  results: StockResult[]
  scanned: number
  returned: number
}

export type ExitReason = "target" | "stop_loss" | "time_exit"

export interface BacktestTrade {
  ticker?: string
  signal_date: string
  entry_price: number
  stop_loss: number
  target: number
  pattern_type: "VCP" | "Bull Flag"
  exit_price: number
  exit_date: string
  exit_reason: ExitReason
  hold_days: number
  pnl_pct: number
  max_loss_pct?: number
  max_profit_pct?: number
}

export interface BacktestStats {
  total_trades: number
  wins: number
  losses: number
  win_rate: number
  avg_return_pct: number
  avg_win_pct: number
  avg_loss_pct: number
  total_return_pct: number
  expectancy: number
  max_drawdown_pct: number
}

export interface BacktestTickerResult {
  ticker: string
  trades: BacktestTrade[]
  stats: BacktestStats
}

export interface BacktestResponse {
  results: BacktestTickerResult[]
  aggregate: BacktestStats
  total_tickers: number
  all_trades: BacktestTrade[]
}
