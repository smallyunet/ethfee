import { useEffect, useState } from 'react';

export function useCountdown(intervalMs: number = 10000) {
  const [remaining, setRemaining] = useState(intervalMs / 1000);

  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => {
      const elapsed = Date.now() - start;
      const next = Math.max(0, intervalMs - elapsed);
      setRemaining(Math.ceil(next / 1000));
    }, 1000);

    return () => clearInterval(id);
  }, [intervalMs]);

  return remaining;
}
