// All code and comments in English                   ──────────────────────────
export interface GasResponse {
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
}

export interface EventsResponse {
  events: {
    threshold: number;
    state: 'above' | 'below';
    timestamp: string;
  }[];
}

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');

export const fetcher = async <T>(path: string): Promise<T> => {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};
