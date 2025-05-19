'use client';

import React from 'react';

/** Renders an ISO-string in the visitor’s local timezone. */
export default function LocalTime({ iso }: { iso: string }) {
  const dt = new Date(iso); // runs in the browser ⇒ local TZ
  return (
    <time dateTime={iso} title={dt.toLocaleString()}>
      {dt.toLocaleTimeString(undefined, { hour12: false })}
    </time>
  );
}
