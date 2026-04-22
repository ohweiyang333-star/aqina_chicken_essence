'use client';

import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import Image from 'next/image';
import { aqinaSiteConfig } from '@/lib/site-config';
import { IMAGES } from '@/lib/image-utils';

export default function Footer() {
  const t = useTranslations('Index');
  const locale = useLocale();
  const homeHref = `/${locale}`;

  return (
    <footer className="border-t border-primary/14 bg-background-dark py-12">
      <div className="section-shell space-y-8">
        <div className="flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
          <div className="space-y-3">
            <Link href={homeHref} className="inline-flex items-center">
              <div className="relative h-14 w-32">
                <Image src={IMAGES.logo} alt="Aqina Logo" fill className="object-contain" sizes="140px" />
              </div>
            </Link>
            <p className="max-w-md text-sm leading-7 text-muted">{t('footer.tagline')}</p>
          </div>

          <nav className="flex flex-wrap gap-4 text-xs font-bold uppercase tracking-[0.22em] text-text-light/72">
            <Link href="#story-experience" className="hover:text-primary">
              {t('footer.nav.story')}
            </Link>
            <Link href="#ugc-reviews" className="hover:text-primary">
              {t('footer.nav.reviews')}
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
