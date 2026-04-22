'use client';

import { useEffect, useMemo, useState } from 'react';

interface CountdownConfig {
  storageKey: string;
  durationMs: number;
}

interface CountdownResult {
  remainingMs: number;
  formatted: string;
  resetAt: number;
}

function pad(value: number) {
  return value.toString().padStart(2, '0');
}

function formatDuration(remainingMs: number) {
  const totalSeconds = Math.max(0, Math.floor(remainingMs / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
}

export default function useEvergreenCountdown({
  storageKey,
  durationMs,
}: CountdownConfig): CountdownResult {
  const [remainingMs, setRemainingMs] = useState(durationMs);
  const [resetAt, setResetAt] = useState(0);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const now = Date.now();
    const storedDeadline = Number(window.localStorage.getItem(storageKey));
    const validStoredDeadline = Number.isFinite(storedDeadline) ? storedDeadline : 0;

    let deadline = validStoredDeadline > now ? validStoredDeadline : now + durationMs;
    window.localStorage.setItem(storageKey, String(deadline));

    const frameId = window.requestAnimationFrame(() => {
      setResetAt(deadline);
      setRemainingMs(Math.max(0, deadline - now));
    });

    const timerId = window.setInterval(() => {
      const current = Date.now();
      let nextRemaining = deadline - current;

      if (nextRemaining <= 0) {
        deadline = current + durationMs;
        window.localStorage.setItem(storageKey, String(deadline));
        setResetAt(deadline);
        nextRemaining = deadline - current;
      }

      setRemainingMs(Math.max(0, nextRemaining));
    }, 1000);

    return () => {
      window.clearInterval(timerId);
      window.cancelAnimationFrame(frameId);
    };
  }, [durationMs, storageKey]);

  const formatted = useMemo(() => formatDuration(remainingMs), [remainingMs]);

  return {
    remainingMs,
    formatted,
    resetAt,
  };
}
