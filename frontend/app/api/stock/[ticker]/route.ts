import { NextRequest, NextResponse } from "next/server"

export async function GET(
  _req: NextRequest,
  { params }: { params: { ticker: string } }
) {
  const fastapiUrl = process.env.FASTAPI_URL || "http://localhost:8000"
  const ticker = params.ticker

  try {
    const res = await fetch(`${fastapiUrl}/api/stock/${encodeURIComponent(ticker)}`)
    if (!res.ok) {
      const text = await res.text()
      return NextResponse.json({ error: text }, { status: res.status })
    }
    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: "Backend unreachable." },
      { status: 503 }
    )
  }
}
