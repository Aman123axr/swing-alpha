"use client"

import { useCallback, useEffect, useState } from "react"
import { RefreshCw, Activity, BookMarked } from "lucide-react"
import { StockResult, SortKey, ScanResponse } from "@/lib/types"
import TopStocks from "@/components/TopStocks"
import StockTable from "@/components/StockTable"
import FilterBar from "@/components/FilterBar"
import UploadCSV from "@/components/UploadCSV"

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? ""

const DEFAULT_TICKERS = [
  "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
  "HINDUNILVR.NS", "BAJFINANCE.NS", "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS",
  "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS", "SUNPHARMA.NS", "WIPRO.NS",
  "ULTRACEMCO.NS", "NESTLEIND.NS", "TECHM.NS", "POWERGRID.NS", "NTPC.NS",
]

const WATCHLIST_KEY = "swing_alpha_watchlist"
const RESULTS_KEY = "swing_alpha_scan_results"
const SCAN_META_KEY = "swing_alpha_scan_meta"
const TICKER_LIST_KEY = "swing_alpha_ticker_list"

export default function Dashboard() {
  const [scanResults, setScanResults] = useState<StockResult[]>([])
  const [isScanning, setIsScanning] = useState(false)
  const [scanStatus, setScanStatus] = useState<string>("")
  const [scanError, setScanError] = useState<string | null>(null)
  const [tickerList, setTickerList] = useState<string[]>(DEFAULT_TICKERS)
  const [csvMode, setCsvMode] = useState(false)
  const [lastScanned, setLastScanned] = useState<number>(0)
  const [lastScannedAt, setLastScannedAt] = useState<string | null>(null)

  const [filterHighConviction, setFilterHighConviction] = useState(false)
  const [sortKey, setSortKey] = useState<SortKey>("total_score")
  const [searchQuery, setSearchQuery] = useState("")
  const [watchlist, setWatchlist] = useState<string[]>([])

  // On mount: restore saved results and watchlist — no auto-scan
  useEffect(() => {
    try {
      const storedWatchlist = localStorage.getItem(WATCHLIST_KEY)
      if (storedWatchlist) setWatchlist(JSON.parse(storedWatchlist))
    } catch {}
    try {
      const storedResults = localStorage.getItem(RESULTS_KEY)
      if (storedResults) {
        const parsed = JSON.parse(storedResults)
        if (Array.isArray(parsed) && parsed.length > 0) {
          setScanResults(parsed)
          setLastScanned(parsed.length)
        }
      }
    } catch {}
    try {
      const meta = localStorage.getItem(SCAN_META_KEY)
      if (meta) setLastScannedAt(JSON.parse(meta))
    } catch {}
    try {
      const storedTickers = localStorage.getItem(TICKER_LIST_KEY)
      if (storedTickers) {
        const parsed = JSON.parse(storedTickers)
        if (Array.isArray(parsed) && parsed.length > 0) {
          setTickerList(parsed)
          setCsvMode(true)
        }
      }
    } catch {}
  }, [])

  const toggleWatchlist = useCallback((ticker: string) => {
    setWatchlist((prev) => {
      const next = prev.includes(ticker)
        ? prev.filter((t) => t !== ticker)
        : [...prev, ticker]
      localStorage.setItem(WATCHLIST_KEY, JSON.stringify(next))
      return next
    })
  }, [])

  const triggerScan = useCallback(
    async (explicitTickers?: string[]) => {
      setIsScanning(true)
      setScanError(null)
      // Clear stale results so the new CSV scan results aren't buried under old ones
      if (explicitTickers) setScanResults([])

      let tickers = explicitTickers ?? tickerList

      // When triggered by button (no explicit tickers) and not in CSV mode, fetch fresh from ChartInk
      if (!explicitTickers && !csvMode) {
        setScanStatus("Fetching stocks from screener…")
        try {
          const ciRes = await fetch(`${BACKEND}/api/chartink/fetch`, { method: "POST" })
          if (ciRes.ok) {
            const ciData = await ciRes.json()
            if (Array.isArray(ciData.tickers) && ciData.tickers.length > 0) {
              tickers = ciData.tickers
              setTickerList(ciData.tickers)
              // Do NOT save ChartInk tickers to localStorage — only CSV tickers persist
            }
          }
        } catch {
          // ChartInk unavailable — proceed with current ticker list
        }
      }

      setScanStatus(`Scanning ${tickers.length} stocks…`)
      try {
        const res = await fetch(`${BACKEND}/api/scan`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tickers }),
        })
        const data: ScanResponse & { error?: string } = await res.json()
        if (!res.ok) throw new Error(data.error || "Scan failed")
        setScanResults(data.results)
        setLastScanned(data.scanned)
        const now = new Date().toISOString()
        setLastScannedAt(now)
        try {
          localStorage.setItem(RESULTS_KEY, JSON.stringify(data.results))
          localStorage.setItem(SCAN_META_KEY, JSON.stringify(now))
        } catch {}
      } catch (e: unknown) {
        setScanError(e instanceof Error ? e.message : String(e))
      } finally {
        setIsScanning(false)
        setScanStatus("")
      }
    },
    [tickerList, csvMode]
  )


  const displayResults = scanResults
    .filter((s) => {
      if (filterHighConviction && s.category !== "High Conviction") return false
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        if (
          !s.ticker.toLowerCase().includes(q) &&
          !s.short_name.toLowerCase().includes(q)
        )
          return false
      }
      return true
    })
    .sort((a, b) => {
      const av = (a[sortKey] ?? 0) as number
      const bv = (b[sortKey] ?? 0) as number
      return bv - av
    })

  const highConvictionCount = scanResults.filter((s) => s.category === "High Conviction").length
  const goodSwingCount = scanResults.filter((s) => s.category === "Good Swing").length
  const watchlistResults = scanResults.filter((s) => watchlist.includes(s.ticker))

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-screen-xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-indigo-400" />
            <span className="font-bold text-lg tracking-tight">Swing Alpha</span>
            <span className="text-xs text-gray-500 hidden sm:block">
              Rule-Based Swing Scanner · NSE/BSE
            </span>
          </div>

          <div className="flex items-center gap-3">
            {lastScannedAt && !isScanning && (
              <span className="text-xs text-gray-500 hidden sm:block">
                Last scan: {new Date(lastScannedAt).toLocaleString()}
              </span>
            )}
            {csvMode && (
              <button
                onClick={() => {
                  setCsvMode(false)
                  setTickerList(DEFAULT_TICKERS)
                  try { localStorage.removeItem(TICKER_LIST_KEY) } catch {}
                }}
                className="text-xs text-indigo-400 hover:text-white border border-indigo-800 hover:border-indigo-500 px-2 py-1 rounded-md transition-colors hidden sm:block"
                title="Clear CSV — switch back to ChartInk screener"
              >
                CSV ({tickerList.length}) ✕
              </button>
            )}
            <UploadCSV
              onTickersLoaded={(tickers) => {
                setTickerList(tickers)
                setCsvMode(true)
                try { localStorage.setItem(TICKER_LIST_KEY, JSON.stringify(tickers)) } catch {}
                triggerScan(tickers)
              }}
            />
            <button
              onClick={() => triggerScan()}
              disabled={isScanning}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isScanning ? "animate-spin" : ""}`} />
              {isScanning ? "Scanning..." : "Refresh Scan"}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-screen-xl mx-auto px-4 py-6 flex flex-col gap-6">
        {!BACKEND && process.env.NODE_ENV === "production" && (
          <div className="bg-yellow-900/30 border border-yellow-600/50 rounded-xl p-3 text-yellow-300 text-sm">
            ⚠️ <strong>NEXT_PUBLIC_BACKEND_URL</strong> is not set — scans will fail.
            Set it to your backend URL in Vercel Environment Variables and redeploy.
          </div>
        )}

        {scanError && (
          <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-4 text-red-300 text-sm">
            <strong>Scan error:</strong> {scanError}
            <br />
            <span className="text-red-400/70 text-xs">
              {BACKEND
                ? `Backend: ${BACKEND} — check if it is running.`
                : "Set NEXT_PUBLIC_BACKEND_URL to your backend URL."}
            </span>
          </div>
        )}

        {isScanning && scanResults.length === 0 && (
          <div className="text-center py-20 text-gray-400">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-indigo-400" />
            <p className="text-base font-medium">{scanStatus || "Preparing scan…"}</p>
            <p className="text-sm text-gray-600 mt-1">
              {csvMode ? `Using your CSV list (${tickerList.length} stocks)` : "Fetching from ChartInk screener…"}
            </p>
          </div>
        )}

        {!isScanning && scanResults.length === 0 && (
          <div className="text-center py-20 text-gray-500">
            <Activity className="w-8 h-8 mx-auto mb-4 text-gray-700" />
            <p className="text-base font-medium">No scan data yet</p>
            <p className="text-sm mt-1">Click <span className="text-indigo-400 font-medium">Refresh Scan</span> to fetch and analyse Nifty 500 stocks</p>
          </div>
        )}

        {displayResults.length > 0 && (
          <TopStocks
            stocks={displayResults}
            watchlist={watchlist}
            onWatchlistToggle={toggleWatchlist}
          />
        )}

        {watchlistResults.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
              <BookMarked className="w-4 h-4" />
              Watchlist ({watchlistResults.length})
            </h2>
            <StockTable
              results={watchlistResults}
              watchlist={watchlist}
              onWatchlistToggle={toggleWatchlist}
              sortKey={sortKey}
              onSortChange={setSortKey}
            />
          </div>
        )}

        {scanResults.length > 0 && (
          <div className="flex flex-col gap-3">
            <FilterBar
              filterHighConviction={filterHighConviction}
              onFilterChange={setFilterHighConviction}
              sortKey={sortKey}
              onSortChange={setSortKey}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              totalScanned={lastScanned || scanResults.length}
              highConvictionCount={highConvictionCount}
              goodSwingCount={goodSwingCount}
            />
            <StockTable
              results={displayResults}
              watchlist={watchlist}
              onWatchlistToggle={toggleWatchlist}
              sortKey={sortKey}
              onSortChange={setSortKey}
            />
          </div>
        )}
      </main>
    </div>
  )
}
