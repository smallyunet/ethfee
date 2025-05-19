'use client';
import React from 'react';

function normaliseIso(iso: string) {
  // if no “Z” or ±hh:mm, assume the string is in UTC and append “Z”
  return /Z|[+-]\d\d:\d\d$/.test(iso) ? iso : iso + 'Z';
}

export default function LocalTime({ iso }: { iso: string }) {
  const dt = new Date(normaliseIso(iso));
  return (
    <time dateTime={iso} title={dt.toString()}>
      {dt.toLocaleTimeString(undefined, { hour12: false })}
    </time>
  );
}
