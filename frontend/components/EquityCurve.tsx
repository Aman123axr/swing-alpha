"use client"

import { BacktestTrade } from "@/lib/types"

interface Props {
  trades: BacktestTrade[]
}

export default function EquityCurve({ trades }: Props) {
  if (trades.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-500 text-sm">
        No trades to display
      </div>
    )
  }

  const W = 800
  const H = 200
  const PAD_L = 52
  const PAD_R = 16
  const PAD_T = 16
  const PAD_B = 32

  // Build cumulative return series starting at 0
  const cumPoints: { x: number; y: number; cum: number }[] = []
  let cum = 0
  cumPoints.push({ x: 0, y: 0, cum: 0 })
  trades.forEach((t, i) => {
    cum += t.pnl_pct
    cumPoints.push({ x: i + 1, y: 0, cum: parseFloat(cum.toFixed(2)) })
  })

  const values = cumPoints.map((p) => p.cum)
  const minV = Math.min(0, ...values)
  const maxV = Math.max(0, ...values)
  const range = maxV - minV || 1
  const n = cumPoints.length

  const toX = (i: number) =>
    PAD_L + ((i / (n - 1)) * (W - PAD_L - PAD_R))
  const toY = (v: number) =>
    PAD_T + ((1 - (v - minV) / range) * (H - PAD_T - PAD_B))

  const zeroY = toY(0)

  // Build SVG path segments, coloring green above zero and red below
  const segments: { d: string; positive: boolean }[] = []
  for (let i = 1; i < cumPoints.length; i++) {
    const x1 = toX(i - 1)
    const y1 = toY(cumPoints[i - 1].cum)
    const x2 = toX(i)
    const y2 = toY(cumPoints[i].cum)
    const positive = cumPoints[i].cum >= 0
    segments.push({ d: `M ${x1.toFixed(1)} ${y1.toFixed(1)} L ${x2.toFixed(1)} ${y2.toFixed(1)}`, positive })
  }

  // Y-axis labels
  const yLabels = [minV, 0, maxV].filter((v, i, arr) => arr.indexOf(v) === i)

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full h-48"
      aria-label="Equity curve"
    >
      {/* Grid lines */}
      {yLabels.map((v) => (
        <g key={v}>
          <line
            x1={PAD_L}
            y1={toY(v)}
            x2={W - PAD_R}
            y2={toY(v)}
            stroke={v === 0 ? "#4b5563" : "#1f2937"}
            strokeDasharray={v === 0 ? "4 4" : "2 4"}
            strokeWidth="1"
          />
          <text
            x={PAD_L - 6}
            y={toY(v) + 4}
            textAnchor="end"
            fontSize="10"
            fill="#6b7280"
          >
            {v > 0 ? `+${v.toFixed(1)}` : v.toFixed(1)}%
          </text>
        </g>
      ))}

      {/* Zero baseline */}
      <line
        x1={PAD_L}
        y1={zeroY}
        x2={W - PAD_R}
        y2={zeroY}
        stroke="#374151"
        strokeWidth="1"
      />

      {/* Shaded area under curve */}
      {n > 1 && (
        <path
          d={`M ${toX(0).toFixed(1)} ${zeroY} ${cumPoints
            .map((p, i) => `L ${toX(i).toFixed(1)} ${toY(p.cum).toFixed(1)}`)
            .join(" ")} L ${toX(n - 1).toFixed(1)} ${zeroY} Z`}
          fill={cumPoints[n - 1].cum >= 0 ? "rgba(99,102,241,0.10)" : "rgba(239,68,68,0.10)"}
        />
      )}

      {/* Curve segments */}
      {segments.map((seg, i) => (
        <path
          key={i}
          d={seg.d}
          fill="none"
          stroke={seg.positive ? "#6366f1" : "#ef4444"}
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
      ))}

      {/* Start dot */}
      <circle cx={toX(0)} cy={toY(0)} r="3" fill="#6b7280" />

      {/* End dot */}
      {n > 1 && (
        <circle
          cx={toX(n - 1)}
          cy={toY(cumPoints[n - 1].cum)}
          r="4"
          fill={cumPoints[n - 1].cum >= 0 ? "#6366f1" : "#ef4444"}
        />
      )}

      {/* Final value label */}
      {n > 1 && (
        <text
          x={toX(n - 1) + 6}
          y={toY(cumPoints[n - 1].cum) + 4}
          fontSize="11"
          fontWeight="600"
          fill={cumPoints[n - 1].cum >= 0 ? "#818cf8" : "#f87171"}
        >
          {cumPoints[n - 1].cum >= 0 ? "+" : ""}
          {cumPoints[n - 1].cum.toFixed(1)}%
        </text>
      )}

      {/* X-axis label */}
      <text
        x={W / 2}
        y={H - 4}
        textAnchor="middle"
        fontSize="10"
        fill="#4b5563"
      >
        Trades (chronological)
      </text>
    </svg>
  )
}
