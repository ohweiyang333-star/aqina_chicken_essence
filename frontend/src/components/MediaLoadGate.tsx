'use client';

import { ReactNode, useEffect, useMemo, useState } from 'react';

interface MediaLoadGateProps {
  children: ReactNode;
  sources: string[];
  cacheKey: string;
  variant?: 'dark' | 'warm';
  minVisibleMs?: number;
  maxWaitMs?: number;
}

function preloadImage(src: string) {
  return new Promise<void>((resolve) => {
    if (!src || typeof window === 'undefined') {
      resolve();
      return;
    }

    const image = new window.Image();
    let settled = false;

    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      resolve();
    };

    image.decoding = 'async';
    image.loading = 'eager';
    image.onload = () => {
      if (typeof image.decode === 'function') {
        image.decode().then(finish).catch(finish);
        return;
      }
      finish();
    };
    image.onerror = finish;
    image.src = src;

    if (image.complete) {
      finish();
    }
  });
}

function hasCompletedMediaGate(cacheKey: string) {
  if (typeof window === 'undefined') {
    return false;
  }

  try {
    return window.sessionStorage.getItem(cacheKey) === 'ready';
  } catch {
    return false;
  }
}

function markCompletedMediaGate(cacheKey: string) {
  try {
    window.sessionStorage.setItem(cacheKey, 'ready');
  } catch {
    // Storage can be unavailable in strict browser privacy modes; the page still needs to reveal.
  }
}

export default function MediaLoadGate({
  children,
  sources,
  cacheKey,
  variant = 'dark',
  minVisibleMs = 900,
  maxWaitMs = 7600,
}: MediaLoadGateProps) {
  const [isReady, setIsReady] = useState(() => hasCompletedMediaGate(cacheKey));
  const [progress, setProgress] = useState(() =>
    hasCompletedMediaGate(cacheKey) ? 100 : 8,
  );
  const uniqueSources = useMemo(
    () => Array.from(new Set(sources.filter(Boolean))),
    [sources],
  );

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    if (hasCompletedMediaGate(cacheKey)) {
      return;
    }

    let isCancelled = false;
    let finishStarted = false;
    let loadedCount = 0;
    let finishTimer: number | undefined;
    const startedAt = window.performance.now();

    const revealPage = () => {
      if (isCancelled) {
        return;
      }

      setProgress(100);
      setIsReady(true);
      markCompletedMediaGate(cacheKey);
    };

    const finishGate = () => {
      if (isCancelled || finishStarted) {
        return;
      }
      finishStarted = true;

      const elapsed = window.performance.now() - startedAt;
      const remaining = Math.max(0, minVisibleMs - elapsed);

      finishTimer = window.setTimeout(() => {
        revealPage();
      }, remaining);
    };

    const timeoutId = window.setTimeout(finishGate, maxWaitMs);

    if (uniqueSources.length === 0) {
      finishGate();
    } else {
      void Promise.all(
        uniqueSources.map((src) =>
          preloadImage(src).finally(() => {
            loadedCount += 1;
            if (!isCancelled) {
              setProgress(
                Math.max(
                  8,
                  Math.round((loadedCount / uniqueSources.length) * 100),
                ),
              );
            }
          }),
        ),
      ).then(() => {
        window.clearTimeout(timeoutId);
        finishGate();
      });
    }

    return () => {
      isCancelled = true;
      window.clearTimeout(timeoutId);
      if (finishTimer) {
        window.clearTimeout(finishTimer);
      }
    };
  }, [cacheKey, maxWaitMs, minVisibleMs, uniqueSources]);

  useEffect(() => {
    if (typeof document === 'undefined') {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    if (!isReady) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = previousOverflow;
    }

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isReady]);

  const isWarm = variant === 'warm';

  return (
    <>
      <div
        className={[
          'transition-opacity duration-700 ease-out',
          isReady ? 'opacity-100' : 'opacity-0',
        ].join(' ')}
      >
        {children}
      </div>

      <div
        aria-hidden={isReady}
        aria-live="polite"
        aria-busy={!isReady}
        role="status"
        className={[
          'fixed inset-0 z-[9999] flex items-center justify-center transition-opacity duration-700',
          isReady ? 'pointer-events-none opacity-0' : 'opacity-100',
          isWarm
            ? 'bg-[#fff7e8] text-[#23170d]'
            : 'bg-[radial-gradient(circle_at_72%_28%,rgba(255,184,0,0.17),transparent_34%),linear-gradient(135deg,#061611,#0b241c_48%,#061611)] text-[#fff7e8]',
        ].join(' ')}
      >
        <div className="w-[min(82vw,24rem)] text-center">
          <p
            className={[
              'font-heading text-4xl font-semibold tracking-[0.12em]',
              isWarm ? 'text-[#9b6b1f]' : 'text-[#f3c663]',
            ].join(' ')}
          >
            AQINA
          </p>
          <p
            className={[
              'mt-4 text-xs font-bold uppercase tracking-[0.24em]',
              isWarm ? 'text-[#6f5a43]' : 'text-[#f9df9d]/82',
            ].join(' ')}
          >
            正在准备完整画面
          </p>
          <div
            className={[
              'mt-7 h-px overflow-hidden',
              isWarm ? 'bg-[#d9b46b]/32' : 'bg-[#f3c663]/22',
            ].join(' ')}
          >
            <div
              className={[
                'h-full transition-[width] duration-300 ease-out',
                isWarm ? 'bg-[#b98220]' : 'bg-[#f3c663]',
              ].join(' ')}
              style={{ width: `${progress}%` }}
            />
          </div>
          <p
            className={[
              'mt-4 text-[0.68rem] font-semibold tracking-[0.18em]',
              isWarm ? 'text-[#8d6221]' : 'text-[#fff7e8]/62',
            ].join(' ')}
          >
            {progress}%
          </p>
        </div>
      </div>
    </>
  );
}
