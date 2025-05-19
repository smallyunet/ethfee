// app/page.tsx
import React from "react";
import Link from "next/link";
import { ArrowUpRightFromSquare, Twitter, Send } from "lucide-react";

type GasResponse = {
  safe: string;
  propose: string;
  fast: string;
  base_fee: string;
  last_block: string;
  last_updated: string;
};

type EventsResponse = {
  events: {
    threshold: number;
    state: "above" | "below";
    last_changed: string;
  }[];
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL;

async function fetchGas(): Promise<GasResponse> {
  const res = await fetch(`${apiUrl}/gas`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch /gas");
  return res.json();
}

async function fetchEvents(): Promise<EventsResponse> {
  const res = await fetch(`${apiUrl}/events`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch /events");
  return res.json();
}

export default async function Home() {
  const [gas, evt] = await Promise.all([fetchGas(), fetchEvents()]);

  return (
    <main className="min-h-screen bg-gradient-to-br from-sky-50 to-indigo-50 flex flex-col items-center px-4 py-12">
      {/* Header */}
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight text-indigo-600">
          ethfee.info
        </h1>
        <p className="mt-2 text-gray-600">
          Real-time Ethereum gas-fee monitor
        </p>
      </header>

      {/* Gas card */}
      <section className="w-full max-w-md bg-white shadow-lg rounded-2xl p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">
          Current Gas Fees
        </h2>
        <ul className="space-y-3">
          {[
            { label: "Safe", value: gas.safe },
            { label: "Propose", value: gas.propose },
            { label: "Fast", value: gas.fast },
          ].map(({ label, value }) => (
            <li
              key={label}
              className="flex justify-between items-center border rounded-lg px-4 py-2"
            >
              <span className="font-medium text-gray-700">{label}</span>
              <span className="font-mono text-indigo-600">{value}</span>
            </li>
          ))}
        </ul>

        <div className="mt-4 text-xs text-gray-500">
          <p>Base fee: {gas.base_fee}</p>
          <p>Block: {gas.last_block}</p>
          <p>Updated: {new Date(gas.last_updated).toLocaleTimeString()}</p>
        </div>
      </section>

      {/* Threshold events */}
      <section className="w-full max-w-md bg-white shadow-md rounded-2xl p-6 mb-10">
        <h2 className="text-lg font-semibold mb-4 text-gray-800">
          Threshold Events
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="pb-2">Threshold</th>
                <th className="pb-2">State</th>
                <th className="pb-2">Since</th>
              </tr>
            </thead>
            <tbody>
              {evt.events.map((e) => (
                <tr key={e.threshold} className="border-t last:border-b">
                  <td className="py-2">{e.threshold} Gwei</td>
                  <td
                    className={`py-2 font-medium ${
                      e.state === "above"
                        ? "text-rose-600"
                        : "text-emerald-600"
                    }`}
                  >
                    {e.state.toUpperCase()}
                  </td>
                  <td className="py-2">
                    {new Date(e.last_changed).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Links */}
      <footer className="flex gap-6">
        <Link
          href="https://x.com/ethfee"
          className="flex items-center gap-2 text-gray-700 hover:text-indigo-600"
          target="_blank"
        >
          <Twitter size={18} />
          X /Twitter
          <ArrowUpRightFromSquare size={14} />
        </Link>

        <Link
          href="https://t.me/ethfeeinfo"
          className="flex items-center gap-2 text-gray-700 hover:text-indigo-600"
          target="_blank"
        >
          <Send size={18} />
          Telegram
          <ArrowUpRightFromSquare size={14} />
        </Link>
      </footer>
    </main>
  );
}
