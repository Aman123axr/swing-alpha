"use client"

import { Upload, FileText } from "lucide-react"
import { useRef, useState } from "react"

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? ""

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

    const formData = new FormData()
    formData.append("file", file)

    try {
      const res = await fetch(`${BACKEND}/api/upload-csv`, { method: "POST", body: formData })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || "Upload failed")
      onTickersLoaded(data.tickers)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
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
        <span className="animate-pulse">Uploading...</span>
      ) : (
        <>
          <Upload className="w-4 h-4" />
          <span>Upload CSV</span>
          <FileText className="w-3 h-3 text-gray-500" />
        </>
      )}
      {error && <span className="text-red-400 ml-2 text-xs">{error}</span>}
    </div>
  )
}
