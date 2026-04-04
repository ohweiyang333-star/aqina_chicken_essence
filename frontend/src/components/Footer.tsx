'use client';

import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import { aqinaSiteConfig } from '@/lib/site-config';

export default function Footer() {
  const t = useTranslations('Index');
  const locale = useLocale();
  const homeHref = `/${locale}`;

  return (
    <footer className="border-t border-primary/14 bg-background-dark py-12">
      <div className="section-shell space-y-8">
        <div className="flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
          <div className="space-y-3">
            <Link href={homeHref} className="inline-flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-md border border-primary/36 bg-surface text-primary">
                <span className="font-heading text-xl font-bold">A</span>
              </div>
              <div>
                <div className="font-heading text-2xl font-semibold tracking-[0.14em] text-primary">
                  AQINA
                </div>
                <div className="text-[10px] font-semibold uppercase tracking-[0.34em] text-muted">
                  Premium Essence
                </div>
              </div>
            </Link>
            <p className="max-w-md text-sm leading-7 text-muted">{t('footer.tagline')}</p>
          </div>

          <nav className="flex flex-wrap gap-4 text-xs font-bold uppercase tracking-[0.22em] text-text-light/72">
            <Link href="#audience" className="hover:text-primary">
              {t('footer.nav.audience')}
            </Link>
            <Link href="#science" className="hover:text-primary">
              {t('footer.nav.science')}
            </Link>
            <Link href="#products" className="hover:text-primary">
              {t('footer.nav.products')}
            </Link>
          </nav>
        </div>

        <div className="gold-divider" />

        <div className="flex flex-col gap-2 text-[11px] uppercase tracking-[0.24em] text-muted md:flex-row md:items-center md:justify-between">
          <p>{t('footer.copyright')}</p>
          <p>
            {t('footer.contactLine', {
              phone: aqinaSiteConfig.contact.whatsappDisplay,
              email: aqinaSiteConfig.contact.email,
            })}
          </p>
        </div>
      </div>
    </footer>
  );
}
