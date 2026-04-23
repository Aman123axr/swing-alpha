import { NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  const fastapiUrl = process.env.FASTAPI_URL || "http://localhost:8000"

  try {
    const formData = await req.formData()
    const res = await fetch(`${fastapiUrl}/api/upload-csv`, {
      method: "POST",
      body: formData,
    })
    if (!res.ok) {
      const text = await res.text()
      return NextResponse.json({ error: text }, { status: res.status })
    }
    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: "Backend unreachable. Make sure FastAPI is running on port 8000." },
      { status: 503 }
    )
  }
}
