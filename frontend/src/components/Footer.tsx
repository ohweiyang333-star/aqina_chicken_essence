'use client';

import { useTranslations, useLocale } from 'next-intl';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { aqinaSiteConfig } from '@/lib/site-config';
import { IMAGES } from '@/lib/image-utils';

export default function Footer() {
  const t = useTranslations('Index');
  const locale = useLocale();
  const pathname = usePathname();
  const homeHref = `/${locale}`;
  const isOfferResetEntry = pathname === '/en' || pathname === '/zh';
  const footerLinks = isOfferResetEntry
    ? [
        {
          href: '#offer-reset-proof',
          label: locale === 'zh' ? '产品证明' : 'Product Proof',
        },
        {
          href: '#offer-reset-qa',
          label: locale === 'zh' ? '购买 Q&A' : 'Buying Q&A',
        },
        {
          href: '#offer-reset-products',
          label: locale === 'zh' ? '配套选择' : 'Choose Pack',
        },
      ]
    : [
        {
          href: '#story-experience',
          label: t('footer.nav.story'),
        },
        {
          href: '#ugc-reviews',
          label: t('footer.nav.reviews'),
        },
        {
          href: '#products',
          label: t('footer.nav.products'),
        },
      ];

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
            {footerLinks.map((link) => (
              <Link key={link.href} href={link.href} className="hover:text-primary">
                {link.label}
              </Link>
            ))}
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
