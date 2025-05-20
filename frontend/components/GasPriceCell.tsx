'use client';

import React, { useEffect, useState } from 'react';
import clsx from 'clsx';
import { usePrevious } from './usePrevious';

export function GasPriceCell({ value, inline = false }: { value: string; inline?: boolean }) {
  const current = parseFloat(value);
  const prev = usePrevious(current);
  const [change, setChange] = useState<'up' | 'down' | null>(null);

  useEffect(() => {
    if (prev === undefined) return;
    if (current > prev) setChange('up');
    else if (current < prev) setChange('down');
    else setChange(null);

    const timeout = setTimeout(() => setChange(null), 1000);
    return () => clearTimeout(timeout);
  }, [current, prev]);

  const className = clsx(
    inline ? 'inline-block' : 'text-right',
    'font-semibold transition-colors duration-500',
    change === 'up' && 'text-red-600',
    change === 'down' && 'text-green-600',
    change === null && 'text-indigo-600'
  );

  return <span className={className}>{current.toFixed(4)}</span>;
}

