'use client';

import { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { BadgeCheck, ShoppingBag } from 'lucide-react';
import { useTranslations } from 'next-intl';

export interface SocialProofEvent {
  name: string;
  minutesAgo: number;
  platform: string;
  boxes: number;
  verified: boolean;
}

interface SocialProofToastProps {
  events: SocialProofEvent[];
  intervalMs?: number;
}

export default function SocialProofToast({
  events,
  intervalMs = 6200,
}: SocialProofToastProps) {
  const t = useTranslations('Index.marketing.socialProof');
  const [activeIndex, setActiveIndex] = useState(0);

  const safeEvents = useMemo(
    () =>
      events.filter(
        (event) =>
          event.name &&
          Number.isFinite(event.minutesAgo) &&
          event.platform &&
          Number.isFinite(event.boxes),
      ),
    [events],
  );

  useEffect(() => {
    if (safeEvents.length <= 1) {
      return;
    }

    const timerId = window.setInterval(() => {
      setActiveIndex((previous) => (previous + 1) % safeEvents.length);
    }, intervalMs);

    return () => {
      window.clearInterval(timerId);
    };
  }, [intervalMs, safeEvents.length]);

  if (!safeEvents.length) {
    return null;
  }

  const event = safeEvents[activeIndex];

  return (
    <aside
      id="social-proof-toast"
      className="pointer-events-none fixed bottom-24 right-4 z-[130] w-[calc(100vw-2rem)] max-w-sm md:bottom-6"
      aria-live="polite"
      aria-atomic="true"
    >
      <AnimatePresence mode="wait">
        <motion.article
          key={`${event.name}-${activeIndex}`}
          initial={{ opacity: 0, y: 16, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 8, scale: 0.98 }}
          transition={{ duration: 0.34, ease: 'easeOut' }}
          className="pointer-events-auto rounded-xl border border-primary/24 bg-background-dark/95 p-4 shadow-[0_20px_40px_rgba(0,0,0,0.4)] backdrop-blur-sm"
        >
          <div className="mb-2 flex items-start justify-between gap-3">
            <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-primary">
              <ShoppingBag size={14} />
              <span>{event.platform}</span>
            </div>
            <div className="inline-flex items-center gap-1 rounded-full bg-emerald-500/85 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-white">
              <BadgeCheck size={11} />
              <span>{event.verified ? t('verifiedPurchase') : t('purchase')}</span>
            </div>
          </div>

          <p className="text-sm leading-6 text-text-light">
            <span className="font-semibold">{event.name}</span>
            <span className="text-text-light/80">
              {' '}
              {t('timePrefix', { minutes: event.minutesAgo })}
              {' '}
            </span>
            <span className="font-semibold text-secondary">
              {event.boxes} {t('boxUnit')}
            </span>
            <span className="text-text-light/80"> {t('boxUnitSuffix')}</span>
          </p>
        </motion.article>
      </AnimatePresence>
    </aside>
  );
}
