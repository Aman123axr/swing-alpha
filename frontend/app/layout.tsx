import type { Metadata } from "next"
import localFont from "next/font/local"
import "./globals.css"

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
})

export const metadata: Metadata = {
  title: "Swing Alpha — Rule-Based Swing Scanner",
  description: "Detect VCP and Bull Flag patterns, score and rank NSE/BSE stocks for swing trading",
}

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} antialiased bg-gray-950 text-white`}>
        {children}
      </body>
    </html>
  )
}
