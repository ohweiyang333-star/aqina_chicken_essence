'use client';

import Link from 'next/link';
import { useLocale } from 'next-intl';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Globe2 } from 'lucide-react';
import Image from 'next/image';
import { IMAGES } from '@/lib/image-utils';

export default function Header() {
  const locale = useLocale();
  const pathname = usePathname();
  const homeHref = `/${locale}`;
  const nextLocale = locale === 'en' ? 'zh' : 'en';
  const languageHref = pathname
    ? pathname.replace(new RegExp(`^/${locale}(?=/|$)`), `/${nextLocale}`)
    : `/${nextLocale}`;
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header
      className={[
        'fixed inset-x-0 top-0 z-[100] border-b transition-all duration-300',
        isScrolled
          ? 'border-primary/18 bg-background-dark/88 shadow-[0_10px_40px_rgba(0,0,0,0.35)] backdrop-blur-md'
          : 'border-transparent bg-background-dark/60 backdrop-blur-sm',
      ].join(' ')}
    >
      <div className="section-shell flex h-16 items-center justify-between gap-4">
        <Link href={homeHref} className="flex items-center">
          <div className="relative h-12 w-28">
            <Image src={IMAGES.logo} alt="Aqina Logo" fill className="object-contain" priority sizes="120px" />
          </div>
        </Link>

        <div className="flex items-center gap-2">
          <a
            href="#products"
            className="inline-flex min-h-10 items-center justify-center rounded-md border border-primary/28 bg-surface px-4 text-xs font-bold uppercase tracking-[0.16em] text-text-light shadow-[0_12px_28px_rgba(0,0,0,0.28)] transition hover:border-primary/48 hover:text-primary"
          >
            {locale === 'zh' ? '选配套' : 'Plans'}
          </a>

          <Link
            id="header-language-switch"
            href={languageHref}
            aria-label={locale === 'en' ? 'Switch to Chinese' : 'Switch to English'}
            className="inline-flex min-h-10 items-center justify-center gap-2 rounded-full border border-primary/28 bg-surface px-3 text-xs font-bold uppercase tracking-[0.16em] text-text-light shadow-[0_12px_28px_rgba(0,0,0,0.28)] transition hover:border-primary/48 hover:text-primary sm:px-4"
          >
            <Globe2 size={15} />
            <span>{locale === 'en' ? '中文' : 'EN'}</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
