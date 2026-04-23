"use client"

import { Star, TrendingUp } from "lucide-react"
import { StockResult } from "@/lib/types"

interface TopStocksProps {
  stocks: StockResult[]
  watchlist: string[]
  onWatchlistToggle: (ticker: string) => void
}

const CATEGORY_COLORS: Record<string, string> = {
  "High Conviction": "text-green-400 bg-green-400/10 border-green-500/30",
  "Good Swing": "text-yellow-400 bg-yellow-400/10 border-yellow-500/30",
  Avoid: "text-red-400 bg-red-400/10 border-red-500/30",
}

const GLOW: Record<string, string> = {
  "High Conviction": "ring-1 ring-green-500/40 shadow-[0_0_20px_rgba(34,197,94,0.15)]",
  "Good Swing": "ring-1 ring-yellow-500/30",
  Avoid: "",
}

export default function TopStocks({ stocks, watchlist, onWatchlistToggle }: TopStocksProps) {
  if (stocks.length === 0) return null

  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
        <TrendingUp className="w-4 h-4" />
        Top Picks
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {stocks.slice(0, 5).map((s) => (
          <div
            key={s.ticker}
            className={`relative bg-gray-900 border border-gray-700 rounded-xl p-4 flex flex-col gap-2 ${GLOW[s.category] ?? ""}`}
          >
            {/* Watchlist star */}
            <button
              onClick={() => onWatchlistToggle(s.ticker)}
              className="absolute top-3 right-3"
            >
              <Star
                className={`w-4 h-4 ${watchlist.includes(s.ticker) ? "fill-yellow-400 text-yellow-400" : "text-gray-600 hover:text-yellow-400"}`}
              />
            </button>

            {/* Ticker + name */}
            <div>
              <div className="font-bold text-white text-sm">{s.ticker.replace(".NS", "").replace(".BO", "")}</div>
              <div className="text-xs text-gray-400 truncate">{s.short_name}</div>
            </div>

            {/* Score */}
            <div className="flex items-end gap-1">
              <span className="text-2xl font-bold text-white">{s.total_score}</span>
              <span className="text-gray-500 text-sm mb-0.5">/10</span>
            </div>

            {/* Category badge */}
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full border w-fit ${CATEGORY_COLORS[s.category]}`}
            >
              {s.category}
            </span>

            {/* Pattern */}
            <div className="text-xs text-gray-400">
              Pattern:{" "}
              <span className={s.pattern_type !== "None" ? "text-indigo-400 font-medium" : "text-gray-500"}>
                {s.pattern_type}
              </span>
            </div>

            {/* Entry / SL */}
            <div className="text-xs flex gap-2 mt-1">
              <div>
                <span className="text-gray-500">Entry </span>
                <span className="text-white font-medium">₹{s.entry.toLocaleString("en-IN")}</span>
              </div>
              <div>
                <span className="text-gray-500">SL </span>
                <span className="text-red-400 font-medium">₹{s.stop_loss.toLocaleString("en-IN")}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
