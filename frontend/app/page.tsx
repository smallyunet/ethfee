import React from "react"

async function getGasData() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL

  const res = await fetch(`${apiUrl}/gas`, {
    cache: "no-store",
  })

  if (!res.ok) {
    throw new Error("Failed to fetch gas data")
  }

  return res.json()
}

export default async function Home() {
  const gasData = await getGasData()

  return (
    <main className="p-10">
      <h1 className="text-3xl font-bold mb-4">Ethereum Gas Fee</h1>
      <pre className="bg-gray-100 p-4 rounded text-sm">
        {JSON.stringify(gasData, null, 2)}
      </pre>
    </main>
  )
}
