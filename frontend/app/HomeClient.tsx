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
import { GasPriceCell } from '@/components/GasPriceCell';
import { fetcher, GasResponse, EventsResponse } from '@/lib/api';

export default function HomeClient() {
  const refreshInterval = 10_000;

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
    <main className="min-h-screen bg-gradient-to-br from-sky-50 to-indigo-50 flex flex-col items-center px-4 py-10">
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
      <header className="mb-6 text-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-indigo-600">ethfee.info</h1>
        <p className="text-sm text-gray-500 mt-1">Real-time Ethereum gas fee monitor</p>
      </header>

      {/* Gas Fee Table */}
      {gas && (
        <section className="w-full max-w-md bg-white shadow-md rounded-xl p-4 sm:p-6 mb-8">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-800 text-center mb-4">
            Ethereum Gas Fees
          </h2>

          <div className="overflow-x-auto">
            <table className="min-w-[360px] w-full text-sm font-mono text-gray-700">
              <thead>
                <tr className="border-b text-gray-500">
                  <th className="text-left py-2 w-1/4 whitespace-nowrap">Type</th>
                  <th className="text-right w-1/4 whitespace-nowrap">
                    Gas<br /><span className="text-[11px]">(Gwei)</span>
                  </th>
                  <th className="text-right w-1/4 whitespace-nowrap">
                    ETH Tx<br /><span className="text-[11px]">($)</span>
                  </th>
                  <th className="text-right w-1/4 whitespace-nowrap">
                    USDT Tx<br /><span className="text-[11px]">($)</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {[
                  {
                    label: 'Safe',
                    gwei: gas.safe,
                    ethUsd: gas.safe_transfer_usd,
                    usdtUsd:
                      gas.eth_price_usd && gas.safe_transfer_usd
                        ? (gas.safe_transfer_usd / 21000) * 65000
                        : 0,
                  },
                  {
                    label: 'Propose',
                    gwei: gas.propose,
                    ethUsd: gas.propose_transfer_usd,
                    usdtUsd:
                      gas.eth_price_usd && gas.propose_transfer_usd
                        ? (gas.propose_transfer_usd / 21000) * 65000
                        : 0,
                  },
                  {
                    label: 'Fast',
                    gwei: gas.fast,
                    ethUsd: gas.fast_transfer_usd,
                    usdtUsd:
                      gas.eth_price_usd && gas.fast_transfer_usd
                        ? (gas.fast_transfer_usd / 21000) * 65000
                        : 0,
                  },
                ].map(({ label, gwei, ethUsd, usdtUsd }) => (
                  <tr key={label} className="hover:bg-gray-50">
                    <td className="py-2 font-semibold">{label}</td>
                    <td className="text-right text-indigo-600 whitespace-nowrap">
                      <GasPriceCell value={gwei} inline />
                    </td>
                    <td className="text-right whitespace-nowrap">${ethUsd?.toFixed(4) ?? '0.0000'}</td>
                    <td className="text-right whitespace-nowrap">${usdtUsd?.toFixed(4) ?? '0.0000'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 text-[11px] sm:text-xs text-center text-gray-500 space-y-1">
            <p>
              Base fee: <GasPriceCell value={gas.base_fee.replace(' Gwei', '')} inline /> Gwei
            </p>
            <p>Block #{gas.last_block}</p>
            <p>Updated: <LocalTime iso={gas.last_updated} /></p>
            {gas.eth_price_usd && <p>ETH price: ${gas.eth_price_usd.toFixed(2)}</p>}
          </div>
        </section>
      )}

      {/* Threshold Events */}
      {evt && (
        <section className="w-full max-w-md bg-white shadow-sm rounded-xl p-4 sm:p-6 mb-8">
          <h2 className="text-base font-semibold text-gray-800 mb-4">Threshold Events</h2>
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
