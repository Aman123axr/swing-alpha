"use client"

import { Search, SlidersHorizontal } from "lucide-react"
import { SortKey } from "@/lib/types"

interface FilterBarProps {
  filterHighConviction: boolean
  onFilterChange: (v: boolean) => void
  sortKey: SortKey
  onSortChange: (k: SortKey) => void
  searchQuery: string
  onSearchChange: (q: string) => void
  totalScanned: number
  highConvictionCount: number
  goodSwingCount: number
}

const SORT_OPTIONS: { label: string; value: SortKey }[] = [
  { label: "Total Score", value: "total_score" },
  { label: "Trend Score", value: "trend_score" },
  { label: "Pattern Score", value: "pattern_score" },
  { label: "Volume Score", value: "volume_score" },
  { label: "Fundamental Score", value: "fund_score" },
  { label: "Price", value: "current_price" },
]

export default function FilterBar({
  filterHighConviction,
  onFilterChange,
  sortKey,
  onSortChange,
  searchQuery,
  onSearchChange,
  totalScanned,
  highConvictionCount,
  goodSwingCount,
}: FilterBarProps) {
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between bg-gray-900 border border-gray-700 rounded-xl p-4">
      {/* Stats */}
      <div className="flex items-center gap-4 text-sm">
        <span className="text-gray-400">
          Scanned: <span className="text-white font-semibold">{totalScanned}</span>
        </span>
        <span className="text-green-400 font-semibold">
          ● {highConvictionCount} High Conviction
        </span>
        <span className="text-yellow-400 font-semibold">
          ● {goodSwingCount} Good Swing
        </span>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search ticker..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-8 pr-3 py-1.5 bg-gray-800 border border-gray-600 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 w-44"
          />
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-gray-400" />
          <select
            value={sortKey}
            onChange={(e) => onSortChange(e.target.value as SortKey)}
            className="bg-gray-800 border border-gray-600 rounded-lg text-sm text-white px-3 py-1.5 focus:outline-none focus:border-indigo-500"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                Sort: {o.label}
              </option>
            ))}
          </select>
        </div>

        {/* High Conviction toggle */}
        <button
          onClick={() => onFilterChange(!filterHighConviction)}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            filterHighConviction
              ? "bg-green-600 text-white"
              : "bg-gray-800 border border-gray-600 text-gray-300 hover:border-green-500"
          }`}
        >
          High Conviction Only
        </button>
      </div>
    </div>
  )
}
