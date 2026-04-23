'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { BadgeCheck, MessageSquareText, ShoppingBag } from 'lucide-react';
import { useTranslations } from 'next-intl';

interface BaseSocialProofEvent {
  name: string;
  minutesAgo: number;
  platform: string;
  verified: boolean;
}

export interface PurchaseSocialProofEvent extends BaseSocialProofEvent {
  type: 'purchase';
  boxes: number;
}

export interface ReviewSocialProofEvent extends BaseSocialProofEvent {
  type: 'review';
  rating: number;
}

export type SocialProofEvent = PurchaseSocialProofEvent | ReviewSocialProofEvent;

interface SocialProofToastProps {
  events?: SocialProofEvent[];
  intervalMs?: number;
}

function shuffleIndices(length: number, avoidFirstIndex: number | null) {
  const indices = Array.from({ length }, (_, index) => index);
  for (let i = indices.length - 1; i > 0; i -= 1) {
    const randomIndex = Math.floor(Math.random() * (i + 1));
    [indices[i], indices[randomIndex]] = [indices[randomIndex], indices[i]];
  }

  if (avoidFirstIndex !== null && indices.length > 1 && indices[0] === avoidFirstIndex) {
    [indices[0], indices[1]] = [indices[1], indices[0]];
  }

  return indices;
}

function parseSocialProofEvents(input: unknown): SocialProofEvent[] {
  if (!Array.isArray(input)) {
    return [];
  }

  const parsed: SocialProofEvent[] = [];

  for (const item of input) {
    if (typeof item !== 'object' || !item) {
      continue;
    }

    const candidate = item as Record<string, unknown>;
    const type = candidate.type;
    const name = candidate.name;
    const minutesAgo = candidate.minutesAgo;
    const platform = candidate.platform;
    const verified = Boolean(candidate.verified);

    if ((type !== 'purchase' && type !== 'review')
      || typeof name !== 'string'
      || typeof platform !== 'string'
      || typeof minutesAgo !== 'number') {
      continue;
    }

    if (type === 'purchase') {
      const boxes = candidate.boxes;
      if (typeof boxes !== 'number') {
        continue;
      }
      parsed.push({
        type,
        name,
        minutesAgo,
        platform,
        boxes,
        verified,
      });
      continue;
    }

    const rating = candidate.rating;
    if (typeof rating !== 'number') {
      continue;
    }
    parsed.push({
      type,
      name,
      minutesAgo,
      platform,
      rating,
      verified,
    });
  }

  return parsed;
}

export default function SocialProofToast({
  events,
  intervalMs = 6800,
}: SocialProofToastProps) {
  const t = useTranslations('Index.marketing.socialProof');
  const [activeIndex, setActiveIndex] = useState(0);
  const translatedEvents = useMemo(() => parseSocialProofEvents(t.raw('events')), [t]);
  const sourceEvents = events && events.length > 0 ? events : translatedEvents;
  const queueRef = useRef<number[]>([]);
  const lastShownIndexRef = useRef<number | null>(null);

  const safeEvents = useMemo(
    () =>
      sourceEvents.filter((event) => {
        if (!event.name || !event.platform || !Number.isFinite(event.minutesAgo)) {
          return false;
        }

        if (event.type === 'review') {
          return Number.isFinite(event.rating) && event.rating > 0;
        }

        return Number.isFinite(event.boxes) && event.boxes > 0;
      }),
    [sourceEvents],
  );

  const refillQueue = useCallback(() => {
    if (safeEvents.length <= 1) {
      queueRef.current = safeEvents.length === 1 ? [0] : [];
      return;
    }
    queueRef.current = shuffleIndices(safeEvents.length, lastShownIndexRef.current);
  }, [safeEvents.length]);

  const getNextIndex = useCallback(() => {
    if (safeEvents.length === 0) {
      return null;
    }
    if (safeEvents.length === 1) {
      return 0;
    }
    if (queueRef.current.length === 0) {
      refillQueue();
    }
    const next = queueRef.current.shift();
    if (typeof next !== 'number') {
      return 0;
    }
    return next;
  }, [refillQueue, safeEvents.length]);

  useEffect(() => {
    queueRef.current = [];
    if (safeEvents.length === 0) {
      lastShownIndexRef.current = null;
      return;
    }
    lastShownIndexRef.current = activeIndex % safeEvents.length;
  }, [activeIndex, safeEvents.length]);

  useEffect(() => {
    if (safeEvents.length <= 1) {
      return;
    }

    const timerId = window.setInterval(() => {
      const nextIndex = getNextIndex();
      if (typeof nextIndex !== 'number') {
        return;
      }
      lastShownIndexRef.current = nextIndex;
      setActiveIndex(nextIndex);
    }, intervalMs);

    return () => {
      window.clearInterval(timerId);
    };
  }, [getNextIndex, intervalMs, safeEvents.length]);

  if (!safeEvents.length) {
    return null;
  }

  const event = safeEvents[activeIndex % safeEvents.length];
  const ratingLabel =
    event.type === 'review'
      ? Number.isInteger(event.rating)
        ? String(event.rating)
        : event.rating.toFixed(1)
      : '';

  return (
    <aside
      id="social-proof-toast"
      className="pointer-events-none fixed bottom-[10.75rem] left-4 right-[5.25rem] z-[136] w-auto md:bottom-6 md:left-auto md:right-6 md:w-[calc(100vw-3rem)] md:max-w-sm"
      aria-live="polite"
      aria-atomic="true"
    >
      <AnimatePresence mode="wait">
        <motion.article
          key={`${event.type}-${event.name}-${activeIndex}`}
          initial={{ opacity: 0, y: 14, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 8, scale: 0.98 }}
          transition={{ duration: 0.34, ease: 'easeOut' }}
          className="pointer-events-auto rounded-xl border border-primary/24 bg-background-dark/95 p-4 shadow-[0_20px_40px_rgba(0,0,0,0.42)] backdrop-blur-sm"
        >
          <div className="mb-2 flex items-start justify-between gap-2">
            <div className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.15em] text-primary">
              {event.type === 'purchase' ? <ShoppingBag size={13} /> : <MessageSquareText size={13} />}
              <span>{event.platform}</span>
              <span className="text-text-light/42">•</span>
              <span>{event.type === 'purchase' ? t('purchaseLabel') : t('reviewLabel')}</span>
            </div>
            <div className="inline-flex items-center gap-1 rounded-full bg-emerald-500/85 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-white">
              <BadgeCheck size={11} />
              <span>{event.verified ? t('verified') : t('unverified')}</span>
            </div>
          </div>

          <p className="text-sm leading-6 text-text-light">
            <span className="font-semibold">{event.name}</span>
            <span className="text-text-light/80"> </span>
            {event.type === 'purchase' ? (
              <span className="text-text-light/84">
                {t('purchaseSentence', {
                  minutes: event.minutesAgo,
                  boxes: event.boxes,
                })}
              </span>
            ) : (
              <span className="text-text-light/84">
                {t('reviewSentence', {
                  minutes: event.minutesAgo,
                  rating: ratingLabel,
                })}
              </span>
            )}
          </p>
        </motion.article>
      </AnimatePresence>
    </aside>
  );
}
