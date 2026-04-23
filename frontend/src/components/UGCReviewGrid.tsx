'use client';

import { useCallback, useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { MessageCircle } from 'lucide-react';

interface UGCReview {
  name: string;
  persona: string;
  source: string;
  content: string;
  image?: string;
}

const fallbackReviewImages = [
  '/ugc/cozy-sofa.jpg',
  '/ugc/home-study.jpg',
  '/ugc/morning-kitchen.jpg',
  '/ugc/office-corner.jpg',
  '/ugc/student-exam.webp',
  '/ugc/yoga-studio.jpg',
  '/ugc/sg-middle-aged-chinese-man.webp',
  '/ugc/sg-middle-aged-malay-woman.webp',
  '/ugc/sg-teenage-chinese-student.webp',
  '/ugc/sg-young-chinese-woman-campus.webp',
  '/ugc/sg-young-indian-office-man.webp',
  '/ugc/sg-young-indian-home-woman.webp',
  '/ugc/sg-young-malay-man-park.webp',
  '/ugc/sg-young-fitness-woman.webp',
  '/ugc/sg-elderly-chinese-woman.webp',
  '/ugc/sg-older-malay-man.webp',
] as const;

const AUTO_SCROLL_SPEED = 0.45;
const AUTO_RESUME_DELAY_MS = 1800;

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
    image: review.image || fallbackReviewImages[index % fallbackReviewImages.length],
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

  const normalizeLoopPosition = useCallback((element: HTMLDivElement) => {
    const half = element.scrollWidth / 2;
    if (!half) {
      return;
    }

    if (element.scrollLeft >= half) {
      element.scrollLeft -= half;
    } else if (element.scrollLeft <= 0) {
      element.scrollLeft += half;
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
    pauseAutoplay();
  }, [pauseAutoplay]);

  useEffect(() => {
    const track = trackRef.current;
    if (!track || reviews.length === 0) {
      return;
    }

    let rafId = 0;

    const animate = () => {
      if (!isAutoplayPausedRef.current && !isDraggingRef.current) {
        track.scrollLeft += AUTO_SCROLL_SPEED;
        normalizeLoopPosition(track);
      }
      rafId = window.requestAnimationFrame(animate);
    };

    rafId = window.requestAnimationFrame(animate);

    return () => {
      window.cancelAnimationFrame(rafId);
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
          <p className="mx-auto max-w-3xl text-sm leading-7 text-muted md:text-base">{t('subtitle')}</p>
          <p className="text-xs font-semibold tracking-[0.08em] text-primary/88">{t('dragHint')}</p>
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
            pauseAutoplay(10000);
            event.preventDefault();
          }}
          onPointerMove={(event) => {
            const track = trackRef.current;
            if (!track || !isDraggingRef.current) {
              return;
            }

            const deltaX = event.clientX - startXRef.current;
            track.scrollLeft = startScrollLeftRef.current - deltaX;

            const half = track.scrollWidth / 2;
            if (half > 0) {
              if (track.scrollLeft >= half) {
                track.scrollLeft -= half;
                startScrollLeftRef.current -= half;
              } else if (track.scrollLeft <= 0) {
                track.scrollLeft += half;
                startScrollLeftRef.current += half;
              }
            }
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
