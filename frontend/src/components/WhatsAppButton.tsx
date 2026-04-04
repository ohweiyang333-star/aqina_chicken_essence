'use client';

import { useTranslations } from 'next-intl';
import { MessageCircle } from 'lucide-react';
import { getWhatsAppHref } from '@/lib/site-config';

export default function WhatsAppButton() {
  const t = useTranslations('Index');

  return (
    <a
      href={getWhatsAppHref()}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={t('mobileCta.whatsappLabel')}
      className="fixed bottom-24 right-4 z-[150] flex h-14 w-14 items-center justify-center rounded-full bg-[#25D366] text-white shadow-[0_14px_36px_rgba(0,0,0,0.32)] hover:scale-105 md:bottom-8 md:right-8 md:h-auto md:w-auto md:gap-3 md:px-5 md:py-4"
    >
      <MessageCircle size={26} />
      <span className="hidden text-sm font-bold tracking-tight md:inline">
        {t('mobileCta.whatsappLabel')}
      </span>
    </a>
  );
}
