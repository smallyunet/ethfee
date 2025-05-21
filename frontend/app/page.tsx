/* Server-side component – runs before HTML is streamed */
import { SWRConfig } from 'swr';
import HomeClient from './HomeClient';
import { fetcher, GasResponse, EventsResponse } from '@/lib/api';

// Cache the server fetch for 10 s
export const revalidate = 10;

export default async function Page() {
  const [gas, events] = await Promise.all([
    fetcher<GasResponse>('/gas'),
    fetcher<EventsResponse>('/events'),
  ]);

  return (
    <SWRConfig value={{ fallback: { '/gas': gas, '/events': events } }}>
      <HomeClient />
    </SWRConfig>
  );
}
