"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Activity, ArrowLeft, Play, ChevronDown, ChevronRight, Zap } from "lucide-react"
import { BacktestResponse, BacktestStats, BacktestTickerResult, BacktestTrade, StockResult } from "@/lib/types"
import EquityCurve from "@/components/EquityCurve"

function StatCard({ label, value, sub, positive }: {
  label: string; value: string; sub?: string; positive?: boolean
}) {
  const color = positive === undefined ? "text-white" : positive ? "text-emerald-400" : "text-red-400"
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}

function exitBadge(reason: string) {
  if (reason === "target")
    return <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-900/50 text-emerald-400">Target</span>
  if (reason === "stop_loss")
    return <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-900/50 text-red-400">Stop Loss</span>
  return <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-800 text-gray-400">Time Exit</span>
}

function TradeTable({ trades, showTicker = false }: { trades: BacktestTrade[]; showTicker?: boolean }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-gray-500 border-b border-gray-800">
            {showTicker && <th className="text-left py-2 px-3 font-medium">Ticker</th>}
            <th className="text-left py-2 px-3 font-medium">Signal</th>
            <th className="text-left py-2 px-3 font-medium">Pattern</th>
            <th className="text-right py-2 px-3 font-medium">Entry</th>
            <th className="text-right py-2 px-3 font-medium">Stop Loss</th>
            <th className="text-right py-2 px-3 font-medium">Target</th>
            <th className="text-right py-2 px-3 font-medium">Exit</th>
            <th className="text-left py-2 px-3 font-medium">Exit Date</th>
            <th className="text-left py-2 px-3 font-medium">Reason</th>
            <th className="text-right py-2 px-3 font-medium">Risk</th>
            <th className="text-right py-2 px-3 font-medium">Days</th>
            <th className="text-right py-2 px-3 font-medium">P&L %</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t, i) => (
            <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-900/40">
              {showTicker && <td className="py-2 px-3 font-mono text-gray-300">{t.ticker ?? "—"}</td>}
              <td className="py-2 px-3 text-gray-400">{t.signal_date}</td>
              <td className="py-2 px-3">
                <span className={`px-1.5 py-0.5 rounded text-xs ${t.pattern_type === "VCP" ? "bg-indigo-900/50 text-indigo-300" : "bg-amber-900/50 text-amber-300"}`}>
                  {t.pattern_type}
                </span>
              </td>
              <td className="py-2 px-3 text-right font-mono text-gray-300">₹{t.entry_price.toLocaleString("en-IN")}</td>
              <td className="py-2 px-3 text-right font-mono text-red-400/80">₹{t.stop_loss.toLocaleString("en-IN")}</td>
              <td className="py-2 px-3 text-right font-mono text-emerald-400/80">₹{t.target.toLocaleString("en-IN")}</td>
              <td className="py-2 px-3 text-right font-mono text-gray-300">₹{t.exit_price.toLocaleString("en-IN")}</td>
              <td className="py-2 px-3 text-gray-400">{t.exit_date}</td>
              <td className="py-2 px-3">{exitBadge(t.exit_reason)}</td>
              <td className="py-2 px-3 text-right font-mono text-red-400/70">
                {t.max_loss_pct !== undefined ? `−${t.max_loss_pct}%` : "—"}
              </td>
              <td className="py-2 px-3 text-right text-gray-400">{t.hold_days}d</td>
              <td className={`py-2 px-3 text-right font-bold font-mono ${t.pnl_pct > 0 ? "text-emerald-400" : t.pnl_pct < 0 ? "text-red-400" : "text-gray-400"}`}>
                {t.pnl_pct > 0 ? "+" : ""}{t.pnl_pct.toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function TickerRow({ result }: { result: BacktestTickerResult }) {
  const [open, setOpen] = useState(false)
  const s = result.stats
  return (
    <div className="border border-gray-800 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-900/60 transition-colors text-left"
      >
        {open ? <ChevronDown className="w-4 h-4 text-gray-500 shrink-0" /> : <ChevronRight className="w-4 h-4 text-gray-500 shrink-0" />}
        <span className="font-mono font-semibold text-sm text-gray-200 w-36 shrink-0">{result.ticker}</span>
        <span className="text-xs text-gray-500 w-20 shrink-0">{s.total_trades} trades</span>
        <span className={`text-xs font-medium w-20 shrink-0 ${s.win_rate >= 50 ? "text-emerald-400" : "text-red-400"}`}>
          {s.win_rate}% WR
        </span>
        <span className={`text-xs font-medium w-24 shrink-0 ${s.avg_return_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
          Avg {s.avg_return_pct >= 0 ? "+" : ""}{s.avg_return_pct}%
        </span>
        <span className={`text-xs font-bold ml-auto ${s.total_return_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
          Total {s.total_return_pct >= 0 ? "+" : ""}{s.total_return_pct}%
        </span>
      </button>
      {open && (
        <div className="border-t border-gray-800 bg-gray-950">
          {result.trades.length > 0
            ? <TradeTable trades={result.trades} />
            : <p className="px-4 py-3 text-sm text-gray-500">No signals detected in the backtest window.</p>
          }
        </div>
      )}
    </div>
  )
}

export default function BacktestPage() {
  const [highConvictionStocks, setHighConvictionStocks] = useState<StockResult[]>([])
  const [rrRatio, setRrRatio] = useState(2.0)
  const [maxHoldDays, setMaxHoldDays] = useState(20)
  const [maxLossPct, setMaxLossPct] = useState(5)
  const [maxProfitPct, setMaxProfitPct] = useState(15)
  const [breakoutOnly, setBreakoutOnly] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<BacktestResponse | null>(null)
  const [showAllTrades, setShowAllTrades] = useState(false)

  useEffect(() => {
    try {
      const raw = localStorage.getItem("swing_alpha_scan_results")
      if (raw) {
        const results: StockResult[] = JSON.parse(raw)
        setHighConvictionStocks(results.filter((s) => s.category === "High Conviction"))
      }
    } catch {}
  }, [])

  const runBacktest = async () => {
    const tickers = highConvictionStocks.map((s) => s.ticker)
    if (tickers.length === 0) return

    setIsRunning(true)
    setError(null)
    setData(null)

    try {
      const res = await fetch("/api/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tickers,
          rr_ratio: rrRatio,
          max_hold_days: maxHoldDays,
          max_loss_pct: maxLossPct,
          max_profit_pct: maxProfitPct,
          breakout_only: breakoutOnly,
        }),
      })
      const json = await res.json()
      if (!res.ok) throw new Error(json.error || "Backtest failed")
      setData(json as BacktestResponse)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setIsRunning(false)
    }
  }

  const noStocks = highConvictionStocks.length === 0

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-screen-xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-indigo-400" />
            <span className="font-bold text-lg tracking-tight">Swing Alpha</span>
            <span className="text-gray-600">/</span>
            <span className="text-sm text-gray-300 font-medium">Backtesting</span>
          </div>
          <Link href="/" className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Scanner
          </Link>
        </div>
      </header>

      <main className="max-w-screen-xl mx-auto px-4 py-6 flex flex-col gap-6">

        {/* Config */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-widest mb-4">
            Backtest Configuration
          </h2>

          {noStocks ? (
            <div className="flex flex-col items-center justify-center py-10 gap-4 text-center">
              <Zap className="w-8 h-8 text-gray-600" />
              <div>
                <p className="text-gray-300 font-medium">No High Conviction stocks found</p>
                <p className="text-sm text-gray-500 mt-1">Run the scanner first to identify High Conviction stocks.</p>
              </div>
              <Link
                href="/"
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl text-sm font-semibold transition-colors"
              >
                Go to Scanner
              </Link>
            </div>
          ) : (
            <div className="flex flex-col gap-5">
              {/* Stock chips */}
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">
                  High Conviction stocks from last scan — {highConvictionStocks.length} stocks
                </p>
                <div className="flex flex-wrap gap-2">
                  {highConvictionStocks.map((s) => (
                    <div
                      key={s.ticker}
                      className="flex items-center gap-1.5 bg-indigo-950/60 border border-indigo-800/50 rounded-lg px-3 py-1.5"
                    >
                      <Zap className="w-3 h-3 text-indigo-400" />
                      <span className="text-sm font-mono text-indigo-200">{s.ticker.replace(".NS", "").replace(".BO", "")}</span>
                      <span className="text-xs text-indigo-400 font-semibold">{s.total_score}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="text-xs text-gray-400 uppercase tracking-wider block mb-2">
                    Risk:Reward Ratio — <span className="text-white font-semibold">1 : {rrRatio.toFixed(1)}</span>
                  </label>
                  <input type="range" min={1.0} max={4.0} step={0.5} value={rrRatio}
                    onChange={(e) => setRrRatio(parseFloat(e.target.value))}
                    className="w-full accent-indigo-500" />
                  <div className="flex justify-between text-xs text-gray-600 mt-1">
                    <span>1.0</span><span>1.5</span><span>2.0</span><span>2.5</span><span>3.0</span><span>3.5</span><span>4.0</span>
                  </div>
                </div>

                <div>
                  <label className="text-xs text-gray-400 uppercase tracking-wider block mb-2">
                    Max Holding Period — <span className="text-white font-semibold">{maxHoldDays} trading days</span>
                  </label>
                  <input type="range" min={5} max={40} step={5} value={maxHoldDays}
                    onChange={(e) => setMaxHoldDays(parseInt(e.target.value))}
                    className="w-full accent-indigo-500" />
                  <div className="flex justify-between text-xs text-gray-600 mt-1">
                    <span>5</span><span>10</span><span>15</span><span>20</span><span>25</span><span>30</span><span>35</span><span>40</span>
                  </div>
                </div>

                <div>
                  <label className="text-xs text-gray-400 uppercase tracking-wider block mb-2">
                    Max Loss per Trade — <span className="text-red-400 font-semibold">−{maxLossPct}%</span>
                    <span className="text-gray-600 normal-case ml-1">(hard stop override)</span>
                  </label>
                  <input type="range" min={2} max={10} step={1} value={maxLossPct}
                    onChange={(e) => setMaxLossPct(parseInt(e.target.value))}
                    className="w-full accent-red-500" />
                  <div className="flex justify-between text-xs text-gray-600 mt-1">
                    <span>2%</span><span>4%</span><span>6%</span><span>8%</span><span>10%</span>
                  </div>
                </div>

                <div>
                  <label className="text-xs text-gray-400 uppercase tracking-wider block mb-2">
                    Max Profit per Trade — <span className="text-emerald-400 font-semibold">+{maxProfitPct}%</span>
                    <span className="text-gray-600 normal-case ml-1">(take-profit ceiling)</span>
                  </label>
                  <input type="range" min={5} max={40} step={5} value={maxProfitPct}
                    onChange={(e) => setMaxProfitPct(parseInt(e.target.value))}
                    className="w-full accent-emerald-500" />
                  <div className="flex justify-between text-xs text-gray-600 mt-1">
                    <span>5%</span><span>10%</span><span>15%</span><span>20%</span><span>25%</span><span>30%</span><span>35%</span><span>40%</span>
                  </div>
                </div>
              </div>

              {/* Breakout-only toggle */}
              <div className="flex items-start gap-3 bg-gray-800/40 border border-gray-700/50 rounded-xl p-4">
                <button
                  onClick={() => setBreakoutOnly((v) => !v)}
                  className={`relative shrink-0 w-10 h-5 rounded-full transition-colors mt-0.5 ${breakoutOnly ? "bg-indigo-600" : "bg-gray-600"}`}
                >
                  <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${breakoutOnly ? "translate-x-5" : "translate-x-0.5"}`} />
                </button>
                <div>
                  <p className="text-sm font-medium text-gray-200">
                    Breakout-Only Entries
                    <span className="ml-2 text-xs text-indigo-400 font-normal">Recommended</span>
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Only trade when price has already cleared the resistance level (confirmed breakout). Filters out pre-breakout setups — fewer trades but significantly higher win rate.
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-500">
                  Walk-forward backtest · ~1 year OHLCV · Entry at next-day open
                </p>
                <button
                  onClick={runBacktest}
                  disabled={isRunning}
                  className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2.5 rounded-xl text-sm font-semibold transition-colors"
                >
                  <Play className={`w-4 h-4 ${isRunning ? "animate-pulse" : ""}`} />
                  {isRunning ? "Running..." : "Run Backtest"}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-4 text-red-300 text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Loading */}
        {isRunning && (
          <div className="text-center py-16 text-gray-400">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-base font-medium">Running walk-forward backtest...</p>
            <p className="text-sm text-gray-600 mt-1">
              Testing {highConvictionStocks.length} High Conviction stocks
            </p>
          </div>
        )}

        {/* Results */}
        {data && !isRunning && (
          <>
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest">
                  Aggregate Results — {data.total_tickers} tickers
                </h2>
                <span className="text-xs text-gray-600">R:R {rrRatio.toFixed(1)} · Max {maxHoldDays}d hold</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                <StatCard label="Total Trades" value={String(data.aggregate.total_trades)} sub={`${data.aggregate.wins}W / ${data.aggregate.losses}L`} />
                <StatCard label="Win Rate" value={`${data.aggregate.win_rate}%`} positive={data.aggregate.win_rate >= 50} />
                <StatCard label="Avg Return" value={`${data.aggregate.avg_return_pct > 0 ? "+" : ""}${data.aggregate.avg_return_pct}%`} positive={data.aggregate.avg_return_pct > 0} sub="Per trade" />
                <StatCard label="Expectancy" value={`${data.aggregate.expectancy > 0 ? "+" : ""}${data.aggregate.expectancy}%`} positive={data.aggregate.expectancy > 0} />
                <StatCard label="Max Drawdown" value={`${data.aggregate.max_drawdown_pct.toFixed(1)}%`} positive={data.aggregate.max_drawdown_pct > -10} />
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">Avg Win</p>
                <p className="text-lg font-bold text-emerald-400">+{data.aggregate.avg_win_pct}%</p>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">Avg Loss</p>
                <p className="text-lg font-bold text-red-400">{data.aggregate.avg_loss_pct}%</p>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">Total Return</p>
                <p className={`text-lg font-bold ${data.aggregate.total_return_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {data.aggregate.total_return_pct >= 0 ? "+" : ""}{data.aggregate.total_return_pct}%
                </p>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">W / L</p>
                <p className="text-lg font-bold text-white">{data.aggregate.wins}W / {data.aggregate.losses}L</p>
              </div>
            </div>

            {data.all_trades.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4">
                  Equity Curve (Cumulative Return %)
                </h2>
                <EquityCurve trades={data.all_trades} />
              </div>
            )}

            <div>
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-3">
                Per-Ticker Breakdown
              </h2>
              <div className="flex flex-col gap-2">
                {data.results
                  .slice()
                  .sort((a, b) => b.stats.total_return_pct - a.stats.total_return_pct)
                  .map((r) => <TickerRow key={r.ticker} result={r} />)}
              </div>
            </div>

            {data.all_trades.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
                <button
                  onClick={() => setShowAllTrades((v) => !v)}
                  className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-800/40 transition-colors"
                >
                  <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest">
                    Full Trade Log ({data.all_trades.length} trades)
                  </h2>
                  {showAllTrades ? <ChevronDown className="w-4 h-4 text-gray-500" /> : <ChevronRight className="w-4 h-4 text-gray-500" />}
                </button>
                {showAllTrades && (
                  <div className="border-t border-gray-800">
                    <TradeTable trades={data.all_trades} showTicker />
                  </div>
                )}
              </div>
            )}

            {data.all_trades.length === 0 && (
              <div className="text-center py-12 text-gray-500 bg-gray-900 border border-gray-800 rounded-2xl">
                <p className="text-base">No trades detected in the backtest window.</p>
                <p className="text-sm mt-1 text-gray-600">Pattern conditions may be too strict for this time period.</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
