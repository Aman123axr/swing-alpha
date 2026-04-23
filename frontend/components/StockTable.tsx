"use client"

import { Star, ChevronUp, ChevronDown } from "lucide-react"
import { StockResult, SortKey } from "@/lib/types"

interface StockTableProps {
  results: StockResult[]
  watchlist: string[]
  onWatchlistToggle: (ticker: string) => void
  sortKey: SortKey
  onSortChange: (k: SortKey) => void
}

const CATEGORY_BADGE: Record<string, string> = {
  "High Conviction": "bg-green-500/20 text-green-400 border border-green-500/30",
  "Good Swing": "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
  Avoid: "bg-red-500/20 text-red-400 border border-red-500/30",
}

const PATTERN_BADGE: Record<string, string> = {
  VCP: "bg-indigo-500/20 text-indigo-300",
  "Bull Flag": "bg-blue-500/20 text-blue-300",
  "Loose Structure": "bg-gray-700 text-gray-400",
  None: "bg-gray-800 text-gray-600",
}

function ScorePip({ value, max }: { value: number; max: number }) {
  const pct = Math.min(100, (value / max) * 100)
  const color =
    pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500"
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-white text-sm font-semibold w-5 text-right">{value}</span>
      <div className="w-12 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function SortHeader({
  label,
  colKey,
  current,
  onClick,
}: {
  label: string
  colKey: SortKey
  current: SortKey
  onClick: (k: SortKey) => void
}) {
  const active = current === colKey
  return (
    <th
      className="px-3 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white select-none whitespace-nowrap"
      onClick={() => onClick(colKey)}
    >
      <span className="flex items-center gap-1">
        {label}
        {active ? (
          <ChevronDown className="w-3 h-3 text-indigo-400" />
        ) : (
          <ChevronUp className="w-3 h-3 text-gray-600" />
        )}
      </span>
    </th>
  )
}

export default function StockTable({
  results,
  watchlist,
  onWatchlistToggle,
  sortKey,
  onSortChange,
}: StockTableProps) {
  if (results.length === 0) {
    return (
      <div className="text-center py-16 text-gray-500">
        No results match the current filters.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-700">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-900 border-b border-gray-700">
          <tr>
            <th className="px-3 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider w-8" />
            <th className="px-3 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Stock
            </th>
            <SortHeader label="Price" colKey="current_price" current={sortKey} onClick={onSortChange} />
            <SortHeader label="Change" colKey="day_change_pct" current={sortKey} onClick={onSortChange} />
            <SortHeader label="Score" colKey="total_score" current={sortKey} onClick={onSortChange} />
            <SortHeader label="Trend" colKey="trend_score" current={sortKey} onClick={onSortChange} />
            <SortHeader label="Pattern" colKey="pattern_score" current={sortKey} onClick={onSortChange} />
            <SortHeader label="Volume" colKey="volume_score" current={sortKey} onClick={onSortChange} />
            <SortHeader label="Fundamen." colKey="fund_score" current={sortKey} onClick={onSortChange} />
            <th className="px-3 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Pattern
            </th>
            <th className="px-3 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Category
            </th>
            <th className="px-3 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Entry
            </th>
            <th className="px-3 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Stop Loss
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {results.map((s) => (
            <tr
              key={s.ticker}
              className="hover:bg-gray-800/50 transition-colors"
            >
              {/* Watchlist star */}
              <td className="px-3 py-3">
                <button onClick={() => onWatchlistToggle(s.ticker)}>
                  <Star
                    className={`w-4 h-4 ${
                      watchlist.includes(s.ticker)
                        ? "fill-yellow-400 text-yellow-400"
                        : "text-gray-700 hover:text-yellow-400"
                    }`}
                  />
                </button>
              </td>

              {/* Stock name */}
              <td className="px-3 py-3">
                <div className="font-semibold text-white">
                  {s.ticker.replace(".NS", "").replace(".BO", "")}
                </div>
                <div className="text-xs text-gray-500 truncate max-w-[120px]">{s.short_name}</div>
              </td>

              {/* Price */}
              <td className="px-3 py-3 text-white font-medium">
                {s.current_price != null ? `₹${s.current_price.toLocaleString("en-IN")}` : "—"}
              </td>

              {/* Day change */}
              <td className="px-3 py-3 font-medium whitespace-nowrap">
                {s.day_change_pct != null ? (
                  <span className={s.day_change_pct >= 0 ? "text-green-400" : "text-red-400"}>
                    {s.day_change_pct >= 0 ? "▲" : "▼"} {Math.abs(s.day_change_pct).toFixed(2)}%
                  </span>
                ) : (
                  <span className="text-gray-600">—</span>
                )}
              </td>

              {/* Total score */}
              <td className="px-3 py-3">
                <div className="flex items-center gap-1">
                  <span
                    className={`text-base font-bold ${
                      s.total_score >= 8
                        ? "text-green-400"
                        : s.total_score >= 6
                        ? "text-yellow-400"
                        : "text-red-400"
                    }`}
                  >
                    {s.total_score}
                  </span>
                  <span className="text-gray-600 text-xs">/10</span>
                </div>
              </td>

              {/* Sub-scores */}
              <td className="px-3 py-3"><ScorePip value={s.trend_score} max={3} /></td>
              <td className="px-3 py-3"><ScorePip value={s.pattern_score} max={2} /></td>
              <td className="px-3 py-3"><ScorePip value={s.volume_score} max={2} /></td>
              <td className="px-3 py-3"><ScorePip value={s.fund_score} max={3} /></td>

              {/* Pattern */}
              <td className="px-3 py-3">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${PATTERN_BADGE[s.pattern_type] ?? ""}`}
                >
                  {s.pattern_type}
                </span>
              </td>

              {/* Category */}
              <td className="px-3 py-3">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-semibold ${CATEGORY_BADGE[s.category] ?? ""}`}
                >
                  {s.category}
                </span>
              </td>

              {/* Entry */}
              <td className="px-3 py-3 text-white font-medium">
                ₹{s.entry.toLocaleString("en-IN")}
              </td>

              {/* Stop Loss */}
              <td className="px-3 py-3 text-red-400 font-medium">
                ₹{s.stop_loss.toLocaleString("en-IN")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
