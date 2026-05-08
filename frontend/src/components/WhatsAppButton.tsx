'use client';

import { useLocale, useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { MessageCircle } from 'lucide-react';
import { getV2WhatsAppHref, getWhatsAppHref } from '@/lib/site-config';
import { trackLandingFunnelEvent } from '@/lib/marketing-analytics';

export default function WhatsAppButton() {
  const t = useTranslations('Index');
  const locale = useLocale();
  const pathname = usePathname();
  const isV2Landing = pathname?.startsWith('/v2/');
  const href = isV2Landing ? getV2WhatsAppHref(locale) : getWhatsAppHref();

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={t('mobileCta.whatsappLabel')}
      onClick={() => {
        if (!isV2Landing) return;

        trackLandingFunnelEvent('whatsapp_cta_click', {
          source: 'v2_floating_whatsapp',
          destination: 'whatsapp',
        });
      }}
      className={[
        'fixed bottom-24 right-4 z-[150] h-14 w-14 items-center justify-center rounded-full bg-[#25D366] text-white shadow-[0_14px_36px_rgba(0,0,0,0.32)] hover:scale-105 md:bottom-8 md:right-8 md:h-auto md:w-auto md:gap-3 md:px-5 md:py-4',
        isV2Landing ? 'hidden md:flex' : 'flex',
      ].join(' ')}
    >
      <MessageCircle size={26} />
      <span className="hidden text-sm font-bold tracking-tight md:inline">
        {t('mobileCta.whatsappLabel')}
      </span>
    </a>
  );
}
