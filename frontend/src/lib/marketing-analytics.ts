'use client';

export const MARKETING_CONSENT_STORAGE_KEY = 'aqina_marketing_consent_v1';
export const MARKETING_CONSENT_CHANGE_EVENT = 'aqina-marketing-consent-change';

export type MarketingConsent = 'accepted' | 'declined';

type GtagValue = string | Date | Record<string, unknown> | boolean | number | undefined;
type GtagFunction = (...args: GtagValue[]) => void;

type MetaPixelFunction = {
  (...args: unknown[]): void;
  callMethod?: (...args: unknown[]) => void;
  loaded?: boolean;
  push?: MetaPixelFunction;
  queue?: unknown[][];
  version?: string;
};

declare global {
  interface Window {
    dataLayer?: GtagValue[][];
    gtag?: GtagFunction;
    fbq?: MetaPixelFunction;
    _fbq?: MetaPixelFunction;
  }
}

export interface MarketingProductEvent {
  productId: string | number;
  productName: string;
  value: number;
  currency?: string;
  quantity?: number;
  packageLabel?: string;
  orderId?: string;
}

let initializedGaMeasurementId = '';
let initializedMetaPixelId = '';

export function getGaMeasurementId() {
  return process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID?.trim() || '';
}

export function getMetaPixelId() {
  return process.env.NEXT_PUBLIC_META_PIXEL_ID?.trim() || '';
}

export function hasMarketingAnalyticsConfig() {
  return Boolean(getGaMeasurementId() || getMetaPixelId());
}

export function isTrackablePath(pathname: string | null | undefined) {
  if (!pathname) return false;
  return !pathname.startsWith('/admin') && !pathname.startsWith('/api');
}

export function readMarketingConsent(): MarketingConsent | null {
  if (typeof window === 'undefined') return null;

  try {
    const storedValue = window.localStorage.getItem(MARKETING_CONSENT_STORAGE_KEY);
    return storedValue === 'accepted' || storedValue === 'declined' ? storedValue : null;
  } catch {
    return null;
  }
}

export function writeMarketingConsent(consent: MarketingConsent) {
  if (typeof window === 'undefined') return;

  try {
    window.localStorage.setItem(MARKETING_CONSENT_STORAGE_KEY, consent);
  } catch {
    // Browsers can block localStorage. The in-memory React state still applies for this visit.
  }
}

export function canTrackMarketingEvent(pathname?: string) {
  if (typeof window === 'undefined') return false;

  return (
    readMarketingConsent() === 'accepted' &&
    hasMarketingAnalyticsConfig() &&
    isTrackablePath(pathname ?? window.location.pathname)
  );
}

export function initializeMarketingAnalytics() {
  if (typeof window === 'undefined') return;

  const gaMeasurementId = getGaMeasurementId();
  const metaPixelId = getMetaPixelId();

  if (gaMeasurementId && initializedGaMeasurementId !== gaMeasurementId) {
    window.dataLayer = window.dataLayer || [];
    window.gtag =
      window.gtag ||
      function gtag(...args: GtagValue[]) {
        window.dataLayer?.push(args);
      };
    window.gtag('js', new Date());
    window.gtag('config', gaMeasurementId, { send_page_view: false });
    initializedGaMeasurementId = gaMeasurementId;
  }

  if (metaPixelId && initializedMetaPixelId !== metaPixelId) {
    if (!window.fbq) {
      const fbq: MetaPixelFunction = (...args) => {
        if (fbq.callMethod) {
          fbq.callMethod(...args);
          return;
        }

        fbq.queue?.push(args);
      };

      fbq.push = fbq;
      fbq.loaded = true;
      fbq.version = '2.0';
      fbq.queue = [];
      window.fbq = fbq;
      window._fbq = fbq;
    }

    window.fbq('init', metaPixelId);
    initializedMetaPixelId = metaPixelId;
  }
}

export function trackPageView(pathname: string) {
  if (!canTrackMarketingEvent(pathname)) return;

  initializeMarketingAnalytics();
  trackGaEvent('page_view', {
    page_path: pathname,
    page_location: window.location.href,
    page_title: document.title,
  });
  trackMetaEvent('PageView');
}

export function trackBeginCheckout(product: MarketingProductEvent) {
  if (!canTrackMarketingEvent()) return;

  const params = productEventParams(product);
  initializeMarketingAnalytics();
  trackGaEvent('begin_checkout', {
    currency: params.currency,
    value: params.value,
    items: [params.gaItem],
  });
  trackMetaEvent('InitiateCheckout', params.meta);
}

export function trackReceiptSubmittedAsAddToCart(product: MarketingProductEvent) {
  if (!canTrackMarketingEvent()) return;

  const params = productEventParams(product);
  initializeMarketingAnalytics();
  trackGaEvent('add_to_cart', {
    currency: params.currency,
    value: params.value,
    items: [params.gaItem],
    order_id: product.orderId,
  });
  trackMetaEvent('AddToCart', {
    ...params.meta,
    order_id: product.orderId,
  });
}

export function trackWhatsAppContact(source = 'whatsapp_link') {
  if (!canTrackMarketingEvent()) return;

  initializeMarketingAnalytics();
  trackGaEvent('generate_lead', {
    method: 'whatsapp',
    source,
  });
  trackMetaEvent('Contact', {
    content_name: 'WhatsApp',
    source,
  });
}

export function isWhatsAppHref(href: string) {
  try {
    const url = new URL(href);
    return url.hostname === 'wa.me' || url.hostname.endsWith('.whatsapp.com');
  } catch {
    return false;
  }
}

function productEventParams(product: MarketingProductEvent) {
  const currency = product.currency || 'SGD';
  const productId = String(product.productId);
  const quantity = product.quantity || 1;
  const value = Number(product.value.toFixed(2));

  return {
    currency,
    value,
    gaItem: {
      item_id: productId,
      item_name: product.productName,
      item_category: product.packageLabel || 'Aqina chicken essence',
      price: value,
      quantity,
    },
    meta: {
      content_ids: [productId],
      content_name: product.productName,
      content_type: 'product',
      currency,
      value,
      num_items: quantity,
    },
  };
}

function trackGaEvent(eventName: string, params: Record<string, unknown>) {
  if (!getGaMeasurementId() || !window.gtag) return;
  window.gtag('event', eventName, params);
}

function trackMetaEvent(eventName: string, params?: Record<string, unknown>) {
  if (!getMetaPixelId() || !window.fbq) return;
  window.fbq('track', eventName, params);
}
