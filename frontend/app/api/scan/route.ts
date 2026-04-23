import { NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  const body = await req.json()
  const fastapiUrl = process.env.FASTAPI_URL || "http://localhost:8000"

  try {
    const res = await fetch(`${fastapiUrl}/api/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const text = await res.text()
      return NextResponse.json({ error: text }, { status: res.status })
    }
    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    return NextResponse.json(
      { error: "Backend unreachable. Make sure FastAPI is running on port 8000." },
      { status: 503 }
    )
  }
}
