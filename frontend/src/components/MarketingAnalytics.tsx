'use client';

import Link from 'next/link';
import Script from 'next/script';
import { usePathname } from 'next/navigation';
import { MouseEvent as ReactMouseEvent, useEffect, useSyncExternalStore } from 'react';
import {
  MARKETING_CONSENT_CHANGE_EVENT,
  getGaMeasurementId,
  getMetaPixelId,
  hasMarketingAnalyticsConfig,
  initializeMarketingAnalytics,
  isTrackablePath,
  isWhatsAppHref,
  readMarketingConsent,
  trackPageView,
  trackWhatsAppContact,
  type MarketingConsent,
  writeMarketingConsent,
} from '@/lib/marketing-analytics';

export default function MarketingAnalytics() {
  const pathname = usePathname();
  const consent = useSyncExternalStore(
    subscribeMarketingConsent,
    readMarketingConsent,
    getServerMarketingConsent,
  );

  const gaMeasurementId = getGaMeasurementId();
  const metaPixelId = getMetaPixelId();
  const hasConfig = hasMarketingAnalyticsConfig();
  const canTrackPage = consent === 'accepted' && isTrackablePath(pathname);
  const shouldShowBanner = consent === null && hasConfig && isTrackablePath(pathname);

  useEffect(() => {
    if (!canTrackPage || !pathname) return;

    initializeMarketingAnalytics();
    trackPageView(pathname);
  }, [canTrackPage, pathname]);

  useEffect(() => {
    if (consent !== 'accepted') return;

    const handleClick = (event: MouseEvent) => {
      const target = event.target instanceof Element ? event.target.closest('a[href]') : null;
      if (!(target instanceof HTMLAnchorElement) || !isWhatsAppHref(target.href)) return;

      trackWhatsAppContact(target.id || 'whatsapp_link');
    };

    document.addEventListener('click', handleClick, { capture: true });
    return () => document.removeEventListener('click', handleClick, { capture: true });
  }, [consent]);

  const handleConsent = (
    nextConsent: MarketingConsent,
    event: ReactMouseEvent<HTMLButtonElement>,
  ) => {
    event.preventDefault();
    writeMarketingConsent(nextConsent);
    window.dispatchEvent(new Event(MARKETING_CONSENT_CHANGE_EVENT));
  };

  return (
    <>
      {canTrackPage && gaMeasurementId ? (
        <Script
          id="google-analytics-loader"
          src={`https://www.googletagmanager.com/gtag/js?id=${gaMeasurementId}`}
          strategy="afterInteractive"
        />
      ) : null}

      {canTrackPage && metaPixelId ? (
        <Script
          id="meta-pixel-loader"
          src="https://connect.facebook.net/en_US/fbevents.js"
          strategy="afterInteractive"
        />
      ) : null}

      {shouldShowBanner ? (
        <section
          id="marketing-consent-banner"
          aria-label="Cookie consent"
          className="fixed inset-x-3 bottom-3 z-[260] mx-auto max-w-3xl rounded-lg border border-primary/25 bg-[#0c1814]/96 p-4 text-text-light shadow-[0_22px_70px_rgba(0,0,0,0.45)] backdrop-blur-md sm:bottom-5 sm:p-5"
        >
          <div className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
            <div className="space-y-2">
              <p className="text-sm font-bold text-primary">Cookie and analytics</p>
              <p className="text-sm leading-6 text-text-light/78">
                We use cookies, GA4, Meta Pixel, and Microsoft Clarity to measure website
                performance, ad effectiveness, and page experience. Tracking starts only after
                you accept.
              </p>
              <Link
                id="marketing-consent-privacy-link"
                href="/privacy-policy"
                className="inline-flex text-sm font-bold text-primary underline-offset-4 hover:underline"
              >
                Privacy policy
              </Link>
            </div>

            <div className="flex flex-col gap-2 sm:flex-row md:justify-end">
              <button
                id="marketing-consent-decline"
                type="button"
                onClick={(event) => handleConsent('declined', event)}
                className="min-h-11 rounded-md border border-text-light/15 px-4 text-sm font-bold text-text-light/80 hover:border-text-light/35 hover:bg-white/5"
              >
                Decline
              </button>
              <button
                id="marketing-consent-accept"
                type="button"
                onClick={(event) => handleConsent('accepted', event)}
                className="min-h-11 rounded-md bg-primary px-5 text-sm font-black text-background-dark shadow-[0_10px_26px_rgba(212,175,55,0.24)] hover:bg-secondary"
              >
                Accept
              </button>
            </div>
          </div>
        </section>
      ) : null}
    </>
  );
}

function subscribeMarketingConsent(onStoreChange: () => void) {
  window.addEventListener('storage', onStoreChange);
  window.addEventListener(MARKETING_CONSENT_CHANGE_EVENT, onStoreChange);

  return () => {
    window.removeEventListener('storage', onStoreChange);
    window.removeEventListener(MARKETING_CONSENT_CHANGE_EVENT, onStoreChange);
  };
}

function getServerMarketingConsent() {
  return null;
}
