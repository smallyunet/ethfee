'use client';

import React from 'react';
import useSWR from 'swr';
import Link from 'next/link';
import {
  Twitter,
  Send,
  ArrowUpRightFromSquare,
  RefreshCw,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import LocalTime from '@/components/LocalTime';
import { useCountdown } from '@/components/useCountdown';

type GasResponse = {
  safe: string;
  propose: string;
  fast: string;
  base_fee: string;
  last_block: string;
  last_updated: string;
  eth_price_usd?: number;
  eth_transfer_usd?: number;
  usdt_transfer_usd?: number;
  safe_transfer_usd?: number;
  propose_transfer_usd?: number;
  fast_transfer_usd?: number;
};

type EventsResponse = {
  events: {
    threshold: number;
    state: 'above' | 'below';
    timestamp: string;
  }[];
};

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');

const fetcher = <T,>(path: string): Promise<T> =>
  fetch(`${API_BASE}${path}`, { cache: 'no-store' }).then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  });

export default function Home() {
  const refreshInterval = 10000;

  const {
    data: gas,
    error: gasErr,
    isLoading: gasLoading,
  } = useSWR<GasResponse>('/gas', fetcher, { refreshInterval });

  const {
    data: evt,
    error: evtErr,
    isLoading: evtLoading,
  } = useSWR<EventsResponse>('/events', fetcher, { refreshInterval });

  const countdown = useCountdown(refreshInterval, gas?.last_updated || 0);

  const loading = gasLoading || evtLoading;
  const error = gasErr || evtErr;

  return (
    <main className="min-h-screen bg-gradient-to-br from-sky-50 to-indigo-50 flex flex-col items-center px-4 py-12">
      {/* Status */}
      <div className="mb-4 flex items-center gap-2 text-sm text-gray-500">
        {loading && <RefreshCw className="h-4 w-4 animate-spin" />}
        {loading && 'Refreshing...'}
        {error && <span className="text-red-500">Error loading data</span>}
        {!loading && !error && (
          <>
            Next refresh in <span className="font-mono text-gray-800">{countdown}s</span>
          </>
        )}
      </div>

      {/* Title */}
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-indigo-600">ethfee.info</h1>
        <p className="text-sm text-gray-500 mt-1">Real-time Ethereum gas fee monitor</p>
      </header>

      {/* Gas Fee Card */}
      {gas && (
        <section className="w-full max-w-md bg-white shadow-md rounded-xl p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 text-center mb-4">
            Ethereum Gas Fees
          </h2>

          <table className="w-full text-sm font-mono text-gray-700">
            <thead>
              <tr className="border-b text-gray-500">
                <th className="text-left py-2">Type</th>
                <th className="text-right">Gas (Gwei)</th>
                <th className="text-right">ETH Tx ($)</th>
                <th className="text-right">USDT Tx ($)</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {[
                {
                  label: 'Safe',
                  gwei: gas.safe,
                  ethUsd: gas.safe_transfer_usd,
                  usdtUsd: gas.eth_price_usd && gas.safe_transfer_usd && (gas.safe_transfer_usd / 21000) * 65000,
                },
                {
                  label: 'Propose',
                  gwei: gas.propose,
                  ethUsd: gas.propose_transfer_usd,
                  usdtUsd: gas.eth_price_usd && gas.propose_transfer_usd && (gas.propose_transfer_usd / 21000) * 65000,
                },
                {
                  label: 'Fast',
                  gwei: gas.fast,
                  ethUsd: gas.fast_transfer_usd,
                  usdtUsd: gas.eth_price_usd && gas.fast_transfer_usd && (gas.fast_transfer_usd / 21000) * 65000,
                },
              ].map(({ label, gwei, ethUsd, usdtUsd }) => (
                <tr key={label} className="hover:bg-gray-50">
                  <td className="py-2 font-semibold">{label}</td>
                  <td className="text-right text-indigo-600">{parseFloat(gwei).toFixed(4)}</td>
                  <td className="text-right">${ethUsd?.toFixed(4) ?? '0.0000'}</td>
                  <td className="text-right">${usdtUsd?.toFixed(4) ?? '0.0000'}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="mt-4 text-xs text-center text-gray-500 space-y-1">
            <p>Base fee: {gas.base_fee} Gwei</p>
            <p>Block #{gas.last_block}</p>
            <p>Updated: <LocalTime iso={gas.last_updated} /></p>
            {gas.eth_price_usd && <p>ETH price: ${gas.eth_price_usd.toFixed(2)}</p>}
          </div>
        </section>
      )}

      {/* Threshold Events */}
      {evt && (
        <section className="w-full max-w-md bg-white shadow-sm rounded-xl p-6 mb-8">
          <h2 className="text-base font-semibold text-gray-800 mb-4">
            Threshold Events
          </h2>
          <ul className="text-sm divide-y">
            {evt.events.map((e, i) => (
              <li key={i} className="py-3">
                <div className="flex items-start gap-2">
                  {e.state === 'above' ? (
                    <TrendingUp className="text-red-500 h-4 w-4 mt-1" />
                  ) : (
                    <TrendingDown className="text-green-500 h-4 w-4 mt-1" />
                  )}
                  <div>
                    <div className="font-medium text-gray-700">
                      {e.state.toUpperCase()} {e.threshold} Gwei
                    </div>
                    <div className="text-xs text-gray-400">
                      <LocalTime iso={e.timestamp} />
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Footer */}
      <footer className="mt-6 text-sm text-gray-500 flex gap-6">
        <Link
          href="https://x.com/ethfee"
          className="flex items-center gap-1 hover:text-indigo-600"
          target="_blank"
        >
          <Twitter size={16} /> X <ArrowUpRightFromSquare size={12} />
        </Link>
        <Link
          href="https://t.me/ethfeeinfo"
          className="flex items-center gap-1 hover:text-indigo-600"
          target="_blank"
        >
          <Send size={16} /> Telegram <ArrowUpRightFromSquare size={12} />
        </Link>
      </footer>
    </main>
  );
}
