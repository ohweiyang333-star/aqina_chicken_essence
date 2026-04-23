'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';
import CheckoutModal from '@/components/CheckoutModal';
import useCartStore from '@/lib/cart-store';
import { IMAGES } from '@/lib/image-utils';
import {
  getProducts,
  toDisplayProduct,
  type DisplayProduct,
} from '@/lib/product-service';
import ProductPricingSection from '@/components/ProductPricingSection';
import MobileFloatingCTA from '@/components/MobileFloatingCTA';
import Footer from '@/components/Footer';
import PromoMarquee from '@/components/PromoMarquee';
import HeroFlashSection from '@/components/HeroFlashSection';
import AuthorityPartnerSection from '@/components/AuthorityPartnerSection';
import UGCReviewGrid from '@/components/UGCReviewGrid';
import StoryExperienceSection from '@/components/StoryExperienceSection';
import SocialProofToast from '@/components/SocialProofToast';

export default function HomePage() {
  const t = useTranslations('Index');
  const locale = useLocale();
  const [selectedProduct, setSelectedProduct] = useState<DisplayProduct | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [products, setProducts] = useState<DisplayProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const addItem = useCartStore((state) => state.addItem);

  useEffect(() => {
    async function loadProducts() {
      const fallbackProducts: DisplayProduct[] = [
        {
          id: 'pack1',
          name: t('products.items.pack1'),
          price: 39.9,
          image: IMAGES.products.box1,
          label: t('products.packSizes.pack1'),
          badge: t('products.badges.pack1'),
        },
        {
          id: 'pack2',
          name: t('products.items.pack2'),
          price: 75.0,
          image: IMAGES.products.box2,
          label: t('products.packSizes.pack2'),
          badge: t('products.badges.pack2'),
          popular: true,
        },
        {
          id: 'pack4',
          name: t('products.items.pack4'),
          price: 149.0,
          image: IMAGES.products.box4,
          label: t('products.packSizes.pack4'),
          badge: t('products.badges.pack4'),
        },
        {
          id: 'pack6',
          name: t('products.items.pack6'),
          price: 219.0,
          image: IMAGES.products.box6,
          label: t('products.packSizes.pack6'),
          badge: t('products.badges.pack6'),
        },
      ];

      try {
        const fetchedProducts = await getProducts();
        if (fetchedProducts.length > 0) {
          const displayProducts = fetchedProducts.map((product) =>
            toDisplayProduct(product, locale),
          );
          setProducts(displayProducts);
        } else {
          setProducts(fallbackProducts);
        }
      } catch (error) {
        console.error('Error loading products:', error);
        setProducts(fallbackProducts);
      } finally {
        setIsLoading(false);
      }
    }

    loadProducts();
  }, [locale, t]);

  const handleBuyNow = (product: DisplayProduct) => {
    setSelectedProduct(product);
    setIsModalOpen(true);
  };

  const handleAddToCart = (product: DisplayProduct) => {
    addItem(product, 1);
  };

  return (
    <main className="page-grid flex min-h-screen flex-col pb-24">
      <PromoMarquee />
      <HeroFlashSection />
      <StoryExperienceSection />
      <UGCReviewGrid />
      <AuthorityPartnerSection />
      <ProductPricingSection
        products={products}
        isLoading={isLoading}
        onAddToCart={handleAddToCart}
        onBuyNow={handleBuyNow}
      />
      <Footer />
      <SocialProofToast />
      <MobileFloatingCTA />
      <CheckoutModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        product={selectedProduct}
      />
    </main>
  );
}
