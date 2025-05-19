'use client';

/*
 * ethfee.info – auto‑refreshing gas‑fee dashboard (client side)
 * ────────────────────────────────────────────────────────────
 * • Refreshes /gas and /events every 10 s with SWR
 * • Falls back to same‑origin requests if NEXT_PUBLIC_API_URL is unset
 * • Shows loading / error state in a tiny status bar
 * • TailwindCSS + lucide‑react icons
 */

import React from 'react';
import useSWR from 'swr';
import Link from 'next/link';
import {
  Twitter,
  Send,
  ArrowUpRightFromSquare,
  RefreshCw,
} from 'lucide-react';
import LocalTime from '@/components/LocalTime';

//════════════════════════════════════════════════════════════
// Types
//════════════════════════════════════════════════════════════
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
    state: 'above' | 'below';
    last_changed: string;
  }[];
};

//════════════════════════════════════════════════════════════
// Generic fetcher (adds base URL, handles errors)
//════════════════════════════════════════════════════════════
const API_BASE = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');

const fetcher = <T,>(path: string): Promise<T> =>
  fetch(`${API_BASE}${path}`, { cache: 'no-store' }).then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  });

//════════════════════════════════════════════════════════════
// Main page component
//════════════════════════════════════════════════════════════
export default function Home() {
  // SWR hooks – 10‑second polling
  const {
    data: gas,
    error: gasErr,
    isLoading: gasLoading,
  } = useSWR<GasResponse>('/gas', fetcher, { refreshInterval: 10_000 });

  const {
    data: evt,
    error: evtErr,
    isLoading: evtLoading,
  } = useSWR<EventsResponse>('/events', fetcher, { refreshInterval: 10_000 });

  const loading = gasLoading || evtLoading;
  const error = gasErr || evtErr;

  return (
    <main className="min-h-screen bg-gradient-to-br from-sky-50 to-indigo-50 flex flex-col items-center px-4 py-12">
      {/* Status bar */}
      <div className="mb-4 flex items-center gap-2 text-sm text-gray-500">
        {loading && <RefreshCw className="h-4 w-4 animate-spin" />}
        {loading && 'Refreshing…'}
        {error && <span className="text-rose-600">Error loading data</span>}
        {!loading && !error && 'Auto‑refresh every 10 s'}
      </div>

      {/* Header */}
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight text-indigo-600">ethfee.info</h1>
        <p className="mt-2 text-gray-600">Real-time Ethereum gas‑fee monitor</p>
      </header>

      {/* Gas card */}
      {gas && (
        <section className="w-full max-w-md bg-white shadow-lg rounded-2xl p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Current Gas Fees</h2>

          <ul className="space-y-3">
            {[
              { label: 'Safe', value: gas.safe },
              { label: 'Propose', value: gas.propose },
              { label: 'Fast', value: gas.fast },
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

          <div className="mt-4 text-xs text-gray-500 space-y-1">
            <p>Base fee: {gas.base_fee}</p>
            <p>Block&nbsp;# {gas.last_block}</p>
            <p>
              Updated: <LocalTime iso={gas.last_updated} />
            </p>
          </div>
        </section>
      )}

      {/* Threshold events */}
      {evt && (
        <section className="w-full max-w-md bg-white shadow-md rounded-2xl p-6 mb-10">
          <h2 className="text-lg font-semibold mb-4 text-gray-800">Threshold Events</h2>

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
                        e.state === 'above' ? 'text-rose-600' : 'text-emerald-600'
                      }`}
                    >
                      {e.state.toUpperCase()}
                    </td>
                    <td className="py-2">
                      <LocalTime iso={e.last_changed} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Links */}
      <footer className="flex gap-6">
        <Link
          href="https://x.com/ethfee"
          className="flex items-center gap-2 text-gray-700 hover:text-indigo-600"
          target="_blank"
        >
          <Twitter size={18} />
          X&nbsp;/&nbsp;Twitter
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
