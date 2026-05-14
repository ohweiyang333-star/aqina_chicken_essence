'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { trackLandingFunnelEvent } from '@/lib/marketing-analytics';

export default function MobileFloatingCTA() {
  const t = useTranslations('Index');
  const pathname = usePathname();
  const heroId = getLandingHeroId(pathname);
  const [isHeroVisible, setIsHeroVisible] = useState(Boolean(heroId));

  useEffect(() => {
    if (!heroId) {
      return;
    }

    const hero = document.getElementById(heroId);
    if (!hero) {
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsHeroVisible(Boolean(entry?.isIntersecting));
      },
      { threshold: 0.08 },
    );

    observer.observe(hero);

    return () => observer.disconnect();
  }, [heroId]);

  if (heroId && isHeroVisible) {
    return null;
  }

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-[140] px-4 md:hidden">
      <div className="pointer-events-auto mx-auto max-w-md rounded-[1.1rem] border border-primary/25 bg-background-dark/92 p-2 shadow-[0_16px_40px_rgba(0,0,0,0.38)] backdrop-blur-md">
        <a
          id="mobile-floating-products-cta"
          href="#products"
          onClick={() => {
            trackLandingFunnelEvent('hero_cta_click', {
              source: 'mobile_floating_products',
              destination: 'products',
            });
          }}
          className="gold-button flex min-h-12 items-center justify-center rounded-[0.9rem] px-4 text-sm font-bold uppercase tracking-[0.2em]"
        >
          {t('mobileCta.label')}
        </a>
      </div>
    </div>
  );
}

function getLandingHeroId(pathname: string | null) {
  if (pathname?.startsWith('/v2/')) return 'v2-hero';
  if (pathname?.startsWith('/v3/')) return 'v3-hero';
  if (pathname?.startsWith('/v4/')) return 'v4-hero';
  return null;
}
