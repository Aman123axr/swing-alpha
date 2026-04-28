"use client"

import { Upload, FileText } from "lucide-react"
import { useRef, useState } from "react"

interface UploadCSVProps {
  onTickersLoaded: (tickers: string[]) => void
}

export default function UploadCSV({ onTickersLoaded }: UploadCSVProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)

  const handleFile = async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      setError("Only .csv files are accepted")
      return
    }
    setError(null)
    setLoading(true)

    try {
      const text = (await file.text()).replace(/^﻿/, "")
      const lines = text.split(/\r?\n/).filter((l) => l.trim())
      if (lines.length === 0) throw new Error("Empty CSV file")

      // Detect ticker column from header, fall back to first column
      const header = lines[0].split(",").map((h) => h.trim().replace(/^"|"$/g, "").toLowerCase())
      const knownCols = ["ticker", "symbol", "stock", "scrip", "nse_symbol", "bse_symbol"]
      const colIdx = Math.max(header.findIndex((h) => knownCols.includes(h)), 0)

      const tickers = lines
        .slice(1)
        .map((line) => {
          const cols = line.split(",")
          return (cols[colIdx] ?? "").trim().replace(/^"|"$/g, "")
        })
        .filter((t) => t.length > 0)
        .map((t) => {
          t = t.toUpperCase()
          // Add .NS suffix if no exchange is specified
          if (!t.includes(".")) t = t + ".NS"
          return t
        })

      if (tickers.length === 0) throw new Error("No valid tickers found in CSV")
      onTickersLoaded(tickers)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to read CSV")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-start gap-1">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          const file = e.dataTransfer.files[0]
          if (file) handleFile(file)
        }}
        onClick={() => inputRef.current?.click()}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm cursor-pointer transition-colors ${
          dragging
            ? "border-indigo-400 bg-indigo-900/20 text-indigo-300"
            : "border-gray-600 bg-gray-800 text-gray-300 hover:border-indigo-500 hover:text-white"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
            e.target.value = ""
          }}
        />
        {loading ? (
          <span className="animate-pulse">Reading CSV…</span>
        ) : (
          <>
            <Upload className="w-4 h-4" />
            <span>Upload CSV</span>
            <FileText className="w-3 h-3 text-gray-500" />
          </>
        )}
      </div>
      {error && (
        <span className="text-red-400 text-xs px-1">{error}</span>
      )}
    </div>
  )
}
