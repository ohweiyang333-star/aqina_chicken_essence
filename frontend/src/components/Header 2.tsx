'use client';

import { useLocale } from 'next-intl';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X, ChevronDown, Globe } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function Header() {
  const locale = useLocale();
  const pathname = usePathname();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleLocale = () => {
    const newLocale = locale === 'en' ? 'zh' : 'en';
    const newPath = pathname.replace(`/${locale}`, `/${newLocale}`);
    window.location.href = newPath;
  };

  return (
    <>
      <header className={`fixed top-0 left-0 w-full z-[100] transition-all duration-500 ${
        isScrolled ? 'bg-ivory/80 backdrop-blur-md py-4 shadow-sm' : 'bg-transparent py-6'
      }`}>
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">

          {/* Logo */}
          <Link href={`/${locale}`} className="flex items-center space-x-2">
            <div className="w-10 h-10 gradient-gold rounded-xl flex items-center justify-center text-white shadow-lg">
              <span className="text-xl font-bold">A</span>
            </div>
            <div className="flex flex-col -space-y-1">
              <span className="text-lg font-bold tracking-tighter text-charcoal">AQINA</span>
              <span className="text-[10px] tracking-[0.2em] font-medium text-charcoal/40 uppercase">Singapore</span>
            </div>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center space-x-10 text-sm font-semibold tracking-wide text-charcoal/80">
            <Link href="#products" className="hover:text-primary transition-colors underline-offset-8 hover:underline">Products</Link>
            <Link href="#story" className="hover:text-primary transition-colors underline-offset-8 hover:underline">Our Story</Link>
            <Link href="#faq" className="hover:text-primary transition-colors underline-offset-8 hover:underline">Help</Link>
          </nav>

          {/* Actions */}
          <div className="flex items-center space-x-4">

            {/* Language Switch */}
            <button
              onClick={toggleLocale}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full border border-charcoal/10 hover:border-primary/40 transition-all text-xs font-bold text-charcoal/70"
            >
              <Globe size={14} className="text-primary" />
              <span className="uppercase">{locale === 'en' ? 'ZH' : 'EN'}</span>
              <ChevronDown size={10} className="text-charcoal/30" />
            </button>

            <Link
              href="#products"
              className="hidden rounded-full bg-charcoal px-5 py-2.5 text-xs font-bold uppercase tracking-[0.16em] text-ivory shadow-lg transition-colors hover:bg-primary sm:inline-flex"
            >
              {locale === 'zh' ? '选配套' : 'Plans'}
            </Link>

            {/* Mobile Menu Trigger */}
            <button className="md:hidden p-2 text-charcoal" onClick={() => setIsMobileMenuOpen(true)}>
              <Menu size={24} />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Drawer */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 bg-charcoal z-[200] p-10 flex flex-col justify-between">
          <div className="flex justify-between items-center">
            <span className="text-white font-bold opacity-30 tracking-widest text-xl">MENU</span>
            <button className="p-2 text-white/50" onClick={() => setIsMobileMenuOpen(false)}>
              <X size={32} />
            </button>
          </div>

          <nav className="flex flex-col space-y-10 text-4xl font-bold text-white">
            <Link href="#products" onClick={() => setIsMobileMenuOpen(false)}>Experience</Link>
            <Link href="#story" onClick={() => setIsMobileMenuOpen(false)}>Origin</Link>
            <Link href="#faq" onClick={() => setIsMobileMenuOpen(false)}>Support</Link>
          </nav>

          <button onClick={toggleLocale} className="text-primary font-bold text-xl flex items-center space-x-2">
             <Globe size={20} />
             <span>Switch to {locale === 'en' ? 'Chinese / 中文' : 'English'}</span>
          </button>
        </div>
      )}
    </>
  );
}
