'use client';

import { useTranslations } from 'next-intl';
import Link from 'next/link';

export default function Footer() {
  const t = useTranslations('Index');

  return (
    <footer className="w-full bg-charcoal pt-24 pb-12 px-6 sm:px-12 text-ivory">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-16 mb-20">

          <div className="space-y-6">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 gradient-gold rounded-lg flex items-center justify-center text-white">
                <span className="font-bold">A</span>
              </div>
              <span className="text-xl font-bold tracking-tighter">AQINA</span>
            </div>
            <p className="text-ivory/50 leading-relaxed">{t('footer.tagline')}</p>
          </div>

          <div className="space-y-6">
            <h4 className="font-bold text-primary uppercase tracking-widest text-xs">{t('footer.contact')}</h4>
            <ul className="space-y-4 text-ivory/70">
              <li>{t('footer.address')}</li>
              <li>WhatsApp: {t('footer.whatsapp')}</li>
              <li>Email: {t('footer.email')}</li>
            </ul>
          </div>

          <div className="space-y-6">
            <h4 className="font-bold text-primary uppercase tracking-widest text-xs">Navigation</h4>
            <nav className="flex flex-col space-y-3 text-ivory/70 font-medium">
              <Link href="#products" className="hover:text-primary transition-colors">Products</Link>
              <Link href="#story" className="hover:text-primary transition-colors">How We Brew</Link>
              <Link href="#faq" className="hover:text-primary transition-colors">Policies</Link>
            </nav>
          </div>
        </div>

        <div className="pt-12 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-6 text-ivory/30 text-[10px] uppercase font-bold tracking-[0.2em]">
          <p>© 2026 Aqina Singapore. Crafted for Excellence.</p>
          <div className="flex space-x-8">
            <Link href="/privacy" className="hover:text-ivory transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-ivory transition-colors">Terms</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
