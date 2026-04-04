'use client';

import Link from 'next/link';
import { useLocale } from 'next-intl';
import { useEffect, useState } from 'react';
import { ShoppingCart } from 'lucide-react';
import Image from 'next/image';
import useCartStore from '@/lib/cart-store';
import { IMAGES } from '@/lib/image-utils';
import CartDrawer from './CartDrawer';

export default function Header() {
  const locale = useLocale();
  const homeHref = `/${locale}`;
  const [isScrolled, setIsScrolled] = useState(false);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const totalItems = useCartStore((state) => state.totalItems);
  const initializeCart = useCartStore((state) => state.initializeCart);

  useEffect(() => {
    initializeCart();
  }, [initializeCart]);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleCheckout = () => {
    setIsCartOpen(false);
    document.getElementById('products')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <>
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

          <button
            type="button"
            onClick={() => setIsCartOpen(true)}
            aria-label="Open cart"
            className="relative inline-flex h-11 w-11 items-center justify-center rounded-full border border-primary/28 bg-surface text-text-light shadow-[0_12px_28px_rgba(0,0,0,0.28)] hover:border-primary/48 hover:text-primary"
          >
            <ShoppingCart size={18} />
            {totalItems > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-secondary px-1 text-[10px] font-bold text-background-dark">
                {totalItems > 9 ? '9+' : totalItems}
              </span>
            )}
          </button>
        </div>
      </header>

      <CartDrawer
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        onCheckout={handleCheckout}
      />
    </>
  );
}
