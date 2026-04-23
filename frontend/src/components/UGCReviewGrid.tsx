'use client';

import { useCallback, useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { MessageCircle } from 'lucide-react';
import { IMAGES } from '@/lib/image-utils';

interface UGCReview {
  name: string;
  persona: string;
  source: string;
  content: string;
  image?: string;
}

const fallbackReviewImages = IMAGES.ugc.reviews;

const AUTO_SCROLL_STEP_PX = 1;
const AUTO_SCROLL_INTERVAL_MS = 22;
const AUTO_RESUME_DELAY_MS = 1800;
const LOOP_EDGE_BUFFER_PX = 2;

function parseReviews(input: unknown): UGCReview[] {
  if (!Array.isArray(input)) {
    return [];
  }

  const parsed: UGCReview[] = [];

  for (const item of input) {
    if (typeof item !== 'object' || !item) {
      continue;
    }

    const name = 'name' in item && typeof item.name === 'string' ? item.name : '';
    const persona = 'persona' in item && typeof item.persona === 'string' ? item.persona : '';
    const source = 'source' in item && typeof item.source === 'string' ? item.source : '';
    const content = 'content' in item && typeof item.content === 'string' ? item.content : '';
    const image = 'image' in item && typeof item.image === 'string' ? item.image : '';

    if (!name || !persona || !source || !content) {
      continue;
    }

    parsed.push({ name, persona, source, content, image });
  }

  return parsed;
}

export default function UGCReviewGrid() {
  const t = useTranslations('Index.marketing.ugcReviews');
  const parsedReviews = parseReviews(t.raw('items'));
  const reviews = parsedReviews.map((review, index) => ({
    ...review,
    // Prefer V2 gallery images when locale JSON still points to legacy local assets.
    image:
      review.image && !review.image.startsWith('/')
        ? review.image
        : fallbackReviewImages[index % fallbackReviewImages.length],
  }));
  const loopReviews = [...reviews, ...reviews];

  const trackRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef(false);
  const isAutoplayPausedRef = useRef(false);
  const startXRef = useRef(0);
  const startScrollLeftRef = useRef(0);
  const resumeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const pauseAutoplay = useCallback((delay = AUTO_RESUME_DELAY_MS) => {
    isAutoplayPausedRef.current = true;
    if (resumeTimerRef.current) {
      clearTimeout(resumeTimerRef.current);
    }
    resumeTimerRef.current = setTimeout(() => {
      isAutoplayPausedRef.current = false;
      resumeTimerRef.current = null;
    }, delay);
  }, []);

  const normalizeLoopPosition = useCallback((element: HTMLDivElement, syncDragAnchor = false) => {
    const half = element.scrollWidth / 2;
    if (half <= element.clientWidth) {
      return;
    }

    if (element.scrollLeft < LOOP_EDGE_BUFFER_PX) {
      element.scrollLeft += half;
      if (syncDragAnchor) {
        startScrollLeftRef.current += half;
      }
      return;
    }

    if (element.scrollLeft > half + LOOP_EDGE_BUFFER_PX) {
      element.scrollLeft -= half;
      if (syncDragAnchor) {
        startScrollLeftRef.current -= half;
      }
    }
  }, []);

  const stopDragging = useCallback((pointerId?: number) => {
    const track = trackRef.current;
    if (!track) {
      return;
    }

    if (pointerId !== undefined && track.hasPointerCapture(pointerId)) {
      track.releasePointerCapture(pointerId);
    }

    isDraggingRef.current = false;
    track.classList.remove('is-dragging');
    normalizeLoopPosition(track);
    pauseAutoplay();
  }, [normalizeLoopPosition, pauseAutoplay]);

  useEffect(() => {
    const track = trackRef.current;
    if (!track || reviews.length === 0) {
      return;
    }

    const initializeTrackPosition = () => {
      const half = track.scrollWidth / 2;
      if (half <= track.clientWidth) {
        return;
      }
      if (track.scrollLeft < LOOP_EDGE_BUFFER_PX) {
        track.scrollLeft = half * 0.35;
      }
      normalizeLoopPosition(track);
    };
    initializeTrackPosition();
    const delayedInitTimerId = window.setTimeout(initializeTrackPosition, 420);

    const intervalId = window.setInterval(() => {
      if (isAutoplayPausedRef.current || isDraggingRef.current) {
        return;
      }

      const half = track.scrollWidth / 2;
      if (half <= track.clientWidth) {
        return;
      }

      track.scrollLeft += AUTO_SCROLL_STEP_PX;
      if (track.scrollLeft > half + LOOP_EDGE_BUFFER_PX) {
        track.scrollLeft -= half;
      }
    }, AUTO_SCROLL_INTERVAL_MS);

    const handleResize = () => {
      initializeTrackPosition();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.clearInterval(intervalId);
      window.clearTimeout(delayedInitTimerId);
      if (resumeTimerRef.current) {
        clearTimeout(resumeTimerRef.current);
        resumeTimerRef.current = null;
      }
    };
  }, [normalizeLoopPosition, reviews.length]);

  if (reviews.length === 0) {
    return null;
  }

  return (
    <section className="py-12" id="ugc-reviews">
      <div className="section-shell space-y-5">
        <div className="space-y-2 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.26em] text-primary">{t('eyebrow')}</p>
          <h2 className="font-heading text-4xl font-semibold text-text-light md:text-5xl">{t('title')}</h2>
        </div>

        <div
          ref={trackRef}
          className="review-interactive-shell"
          onPointerDown={(event) => {
            if (event.pointerType === 'mouse' && event.button !== 0) {
              return;
            }

            const track = trackRef.current;
            if (!track) {
              return;
            }

            isDraggingRef.current = true;
            startXRef.current = event.clientX;
            startScrollLeftRef.current = track.scrollLeft;
            track.classList.add('is-dragging');
            track.setPointerCapture(event.pointerId);
            pauseAutoplay(9000);
            event.preventDefault();
          }}
          onPointerMove={(event) => {
            const track = trackRef.current;
            if (!track || !isDraggingRef.current) {
              return;
            }

            const deltaX = event.clientX - startXRef.current;
            track.scrollLeft = startScrollLeftRef.current - deltaX;
            normalizeLoopPosition(track, true);
          }}
          onPointerUp={(event) => stopDragging(event.pointerId)}
          onPointerCancel={(event) => stopDragging(event.pointerId)}
          onWheel={() => pauseAutoplay(2600)}
        >
          <div className="review-interactive-track">
            {loopReviews.map((review, index) => (
              <article
                key={`${review.name}-${review.source}-${review.image}-${index}`}
                className="surface-panel min-w-[18rem] max-w-[18rem] overflow-hidden rounded-2xl border border-primary/22 sm:min-w-[20rem] sm:max-w-[20rem] lg:min-w-[22rem] lg:max-w-[22rem]"
              >
                <div className="relative aspect-[16/10]">
                  <Image
                    src={review.image}
                    alt={`${review.name} testimonial`}
                    fill
                    priority={index < reviews.length}
                    sizes="(max-width: 640px) 76vw, (max-width: 1024px) 44vw, 22rem"
                    className="pointer-events-none select-none object-cover"
                  />
                </div>

                <div className="space-y-3 px-4 py-4">
                  <p className="text-sm leading-7 text-text-light/86">“{review.content}”</p>
                  <div className="gold-divider" />

                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-text-light">{review.name}</p>
                      <p className="text-xs text-muted">{review.persona}</p>
                    </div>

                    <div className="inline-flex items-center gap-1 rounded-full border border-primary/22 bg-background-dark/52 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-primary">
                      <MessageCircle size={11} />
                      <span>{review.source}</span>
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
