'use client';

export const MARKETING_CONSENT_STORAGE_KEY = 'aqina_marketing_consent_v1';
export const MARKETING_CONSENT_CHANGE_EVENT = 'aqina-marketing-consent-change';

export type MarketingConsent = 'accepted' | 'declined';
export type MarketingLandingVersion = 'offer_reset' | 'v2' | 'v3' | 'v4';
export type MarketingLanguage = 'en' | 'zh';

type GtagValue = string | Date | Record<string, unknown> | boolean | number | undefined;
type GtagFunction = (...args: GtagValue[]) => void;
type DataLayerCommand = GtagValue[] | IArguments;

type MetaPixelFunction = {
  (...args: unknown[]): void;
  callMethod?: (...args: unknown[]) => void;
  loaded?: boolean;
  push?: MetaPixelFunction;
  queue?: unknown[][];
  version?: string;
};

type ClarityFunction = {
  (...args: unknown[]): void;
  q?: unknown[][];
};

declare global {
  interface Window {
    dataLayer?: DataLayerCommand[];
    gtag?: GtagFunction;
    fbq?: MetaPixelFunction;
    _fbq?: MetaPixelFunction;
    clarity?: ClarityFunction;
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
  eventId?: string;
}

export interface MarketingPageContext {
  page_path: string;
  landing_version?: MarketingLandingVersion;
  language?: MarketingLanguage;
}

export type MarketingFunnelEventName =
  | 'landing_page_view'
  | 'hero_cta_click'
  | 'whatsapp_cta_click'
  | 'product_card_view'
  | 'product_buy_click'
  | 'checkout_open'
  | 'checkout_whatsapp_fallback_click'
  | 'receipt_upload_start'
  | 'checkout_submit_success'
  | 'checkout_submit_error';

export interface MarketingServerEventContext extends MarketingPageContext {
  marketing_consent: MarketingConsent;
  marketing_event_id: string;
  event_source_url: string;
  marketing_fbp?: string;
  marketing_fbc?: string;
}

let initializedGaMeasurementId = '';
let initializedMetaPixelId = '';
let initializedClarityProjectId = '';

export function getGaMeasurementId() {
  return process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID?.trim() || '';
}

export function getMetaPixelId() {
  return process.env.NEXT_PUBLIC_META_PIXEL_ID?.trim() || '';
}

export function getClarityProjectId() {
  return process.env.NEXT_PUBLIC_CLARITY_PROJECT_ID?.trim() || '';
}

export function hasMarketingAnalyticsConfig() {
  return Boolean(getGaMeasurementId() || getMetaPixelId() || getClarityProjectId());
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
  const clarityProjectId = getClarityProjectId();

  if (gaMeasurementId && initializedGaMeasurementId !== gaMeasurementId) {
    window.dataLayer = window.dataLayer || [];
    window.gtag =
      window.gtag ||
      function gtag() {
        // Match Google's official gtag snippet: it queues the arguments object, not a copied array.
        // eslint-disable-next-line prefer-rest-params
        window.dataLayer?.push(arguments);
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

  if (clarityProjectId && initializedClarityProjectId !== clarityProjectId) {
    if (!window.clarity) {
      const clarity: ClarityFunction = (...args) => {
        clarity.q?.push(args);
      };
      clarity.q = [];
      window.clarity = clarity;
    }

    const scriptId = `clarity-loader-${clarityProjectId}`;
    if (!document.getElementById(scriptId)) {
      const script = document.createElement('script');
      script.id = scriptId;
      script.async = true;
      script.src = `https://www.clarity.ms/tag/${clarityProjectId}`;
      script.setAttribute('data-clarity-project-id', clarityProjectId);
      document.head.appendChild(script);
    }

    window.clarity('consentv2', {
      ad_Storage: 'granted',
      analytics_Storage: 'granted',
    });
    initializedClarityProjectId = clarityProjectId;
  }
}

export function trackPageView(pathname: string) {
  if (!canTrackMarketingEvent(pathname)) return;

  const pageContext = getMarketingPageContext(pathname);
  const attributionContext = getMarketingAttributionContext();
  initializeMarketingAnalytics();
  trackGaEvent('page_view', {
    ...pageContext,
    ...attributionContext,
    page_location: window.location.href,
    page_title: document.title,
  });
  trackGaEvent('landing_page_view', {
    ...pageContext,
    ...attributionContext,
    page_location: window.location.href,
  });
  trackMetaEvent('PageView', { ...pageContext, ...attributionContext });
  setClarityContext(pageContext);
}

export function trackBeginCheckout(product: MarketingProductEvent) {
  if (!canTrackMarketingEvent()) return;

  const pageContext = getMarketingPageContext();
  const attributionContext = getMarketingAttributionContext();
  const params = productEventParams(product);
  initializeMarketingAnalytics();
  trackGaEvent('begin_checkout', {
    ...pageContext,
    ...attributionContext,
    currency: params.currency,
    value: params.value,
    items: [params.gaItem],
  });
  trackMetaEvent('InitiateCheckout', {
    ...params.meta,
    ...pageContext,
    ...attributionContext,
  });
}

export function trackReceiptSubmittedAsAddToCart(product: MarketingProductEvent) {
  if (!canTrackMarketingEvent()) return;

  const pageContext = getMarketingPageContext();
  const attributionContext = getMarketingAttributionContext();
  const params = productEventParams(product);
  initializeMarketingAnalytics();
  trackGaEvent('add_to_cart', {
    ...pageContext,
    ...attributionContext,
    currency: params.currency,
    value: params.value,
    items: [params.gaItem],
    event_id: product.eventId,
    order_id: product.orderId,
  });
  trackMetaEvent('AddToCart', {
    ...params.meta,
    ...pageContext,
    ...attributionContext,
    order_id: product.orderId,
  }, product.eventId);
}

export function trackWhatsAppContact(source = 'whatsapp_link') {
  if (!canTrackMarketingEvent()) return;

  const pageContext = getMarketingPageContext();
  const attributionContext = getMarketingAttributionContext();
  initializeMarketingAnalytics();
  trackGaEvent('generate_lead', {
    ...pageContext,
    ...attributionContext,
    method: 'whatsapp',
    source,
  });
  trackMetaEvent('Contact', {
    ...pageContext,
    ...attributionContext,
    content_name: 'WhatsApp',
    source,
  });
  trackMetaEvent('Lead', {
    ...pageContext,
    ...attributionContext,
    content_name: 'WhatsApp consultation',
    source,
  });
}

export function trackLandingFunnelEvent(
  eventName: MarketingFunnelEventName,
  params: Record<string, unknown> = {},
) {
  if (!canTrackMarketingEvent()) return;

  const pageContext = getMarketingPageContext();
  const attributionContext = getMarketingAttributionContext();
  const eventParams = {
    ...pageContext,
    ...attributionContext,
    ...params,
  };

  initializeMarketingAnalytics();
  trackGaEvent(eventName, eventParams);
  trackMetaEvent(eventName, eventParams, undefined, 'trackCustom');
  trackClarityEvent(eventName);
}

export function getMarketingPageContext(pathname?: string): MarketingPageContext {
  const pagePath = normalizeMarketingPath(
    pathname ?? (typeof window === 'undefined' ? '/' : window.location.pathname),
  );
  const segments = pagePath.split('/').filter(Boolean);
  const firstSegment = segments[0];
  const secondSegment = segments[1];

  if (isMarketingLanguage(firstSegment) && segments.length === 1) {
    return {
      page_path: pagePath,
      landing_version: 'offer_reset',
      language: firstSegment,
    };
  }

  if (isMarketingLandingVersion(firstSegment) && isMarketingLanguage(secondSegment)) {
    return {
      page_path: pagePath,
      landing_version: firstSegment,
      language: secondSegment,
    };
  }

  return { page_path: pagePath };
}

export function createMarketingEventId(prefix: string) {
  const safePrefix = prefix.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 48) || 'event';
  const randomPart =
    typeof window !== 'undefined' && window.crypto?.randomUUID
      ? window.crypto.randomUUID()
      : `${Date.now()}_${Math.random().toString(36).slice(2)}`;

  return `${safePrefix}_${randomPart}`;
}

export function getMarketingServerEventContext(
  eventId: string,
): MarketingServerEventContext | null {
  if (!canTrackMarketingEvent()) return null;

  const pageContext = getMarketingPageContext();
  const fbp = readCookieValue('_fbp');
  const fbc = readCookieValue('_fbc') || buildFbcFromUrl();

  return {
    ...pageContext,
    marketing_consent: 'accepted',
    marketing_event_id: eventId,
    event_source_url: window.location.href,
    marketing_fbp: fbp,
    marketing_fbc: fbc,
  };
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

function trackMetaEvent(
  eventName: string,
  params?: Record<string, unknown>,
  eventId?: string,
  command: 'track' | 'trackCustom' = 'track',
) {
  if (!getMetaPixelId() || !window.fbq) return;

  if (eventId) {
    window.fbq(command, eventName, params, { eventID: eventId });
    return;
  }

  window.fbq(command, eventName, params);
}

function trackClarityEvent(eventName: string) {
  if (!getClarityProjectId() || !window.clarity) return;
  window.clarity('event', eventName);
}

function setClarityContext(pageContext: MarketingPageContext) {
  if (!getClarityProjectId() || !window.clarity) return;

  window.clarity('set', 'page_path', pageContext.page_path);
  if (pageContext.landing_version) {
    window.clarity('set', 'landing_version', pageContext.landing_version);
  }
  if (pageContext.language) {
    window.clarity('set', 'language', pageContext.language);
  }
}

function getMarketingAttributionContext() {
  if (typeof window === 'undefined') return {};

  const params = new URLSearchParams(window.location.search);
  const context: Record<string, string> = {};

  for (const key of ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']) {
    const value = params.get(key);
    if (value) {
      context[key] = value;
    }
  }

  const fbclid = params.get('fbclid');
  if (fbclid) {
    context.fbclid = fbclid;
  }

  const fbc = readCookieValue('_fbc') || buildFbcFromUrl();
  if (fbc) {
    context.fbc = fbc;
  }

  return context;
}

function normalizeMarketingPath(pathname: string) {
  const trimmedPath = pathname.trim() || '/';

  if (trimmedPath.startsWith('http://') || trimmedPath.startsWith('https://')) {
    try {
      return new URL(trimmedPath).pathname || '/';
    } catch {
      return '/';
    }
  }

  const [pathWithoutQuery] = trimmedPath.split(/[?#]/);
  if (!pathWithoutQuery) return '/';

  return pathWithoutQuery.startsWith('/') ? pathWithoutQuery : `/${pathWithoutQuery}`;
}

function isMarketingLandingVersion(value: string | undefined): value is MarketingLandingVersion {
  return value === 'v2' || value === 'v3' || value === 'v4';
}

function isMarketingLanguage(value: string | undefined): value is MarketingLanguage {
  return value === 'en' || value === 'zh';
}

function readCookieValue(name: string) {
  if (typeof document === 'undefined') return undefined;

  const encodedName = `${encodeURIComponent(name)}=`;
  const cookie = document.cookie
    .split('; ')
    .find((part) => part.startsWith(encodedName));
  if (!cookie) return undefined;

  const value = cookie.slice(encodedName.length);
  return value ? decodeURIComponent(value) : undefined;
}

function buildFbcFromUrl() {
  if (typeof window === 'undefined') return undefined;

  const fbclid = new URLSearchParams(window.location.search).get('fbclid');
  if (!fbclid) return undefined;

  return `fb.1.${Date.now()}.${fbclid}`;
}
