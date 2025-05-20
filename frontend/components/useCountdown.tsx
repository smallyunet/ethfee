'use client';

import { useEffect, useState } from 'react';

/**
 * Countdown timer that resets when `resetTrigger` changes.
 *
 * @param intervalMs - countdown interval in milliseconds
 * @param resetTrigger - any value that causes countdown to reset when changed
 * @returns number of seconds remaining
 */
export function useCountdown(intervalMs: number, resetTrigger: any): number {
  const [remaining, setRemaining] = useState(intervalMs / 1000);

  // Reset countdown when trigger changes
  useEffect(() => {
    setRemaining(intervalMs / 1000);
  }, [resetTrigger, intervalMs]);

  // Countdown ticking every second
  useEffect(() => {
    const timer = setInterval(() => {
      setRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return remaining;
}
