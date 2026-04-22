'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useEffect, useMemo, useState } from 'react';
import CheckoutModal from '@/components/CheckoutModal';
import useCartStore from '@/lib/cart-store';
import { IMAGES } from '@/lib/image-utils';
import {
  getProducts,
  toDisplayProduct,
  type DisplayProduct,
} from '@/lib/product-service';
import TargetAudienceSection from '@/components/TargetAudienceSection';
import ScienceEndorsementSection from '@/components/ScienceEndorsementSection';
import ProductPricingSection from '@/components/ProductPricingSection';
import MobileFloatingCTA from '@/components/MobileFloatingCTA';
import Footer from '@/components/Footer';
import PromoMarquee from '@/components/PromoMarquee';
import HeroFlashSection from '@/components/HeroFlashSection';
import TrustStatsStrip from '@/components/TrustStatsStrip';
import UGCPhotoTicker from '@/components/UGCPhotoTicker';
import AuthorityPartnerSection from '@/components/AuthorityPartnerSection';
import ShippingCountdownSection from '@/components/ShippingCountdownSection';
import UGCReviewGrid from '@/components/UGCReviewGrid';
import SocialProofToast, { type SocialProofEvent } from '@/components/SocialProofToast';
import {
  NlpMiddleStorySection,
  NlpPriceReframeSection,
  NlpTakeawaySection,
} from '@/components/NlpStorySections';

function parseSocialProofEvents(input: unknown): SocialProofEvent[] {
  if (!Array.isArray(input)) {
    return [];
  }

  return input
    .map((item) => {
      if (typeof item !== 'object' || !item) {
        return null;
      }

      const name = 'name' in item && typeof item.name === 'string' ? item.name : '';
      const minutesAgo = 'minutesAgo' in item ? Number(item.minutesAgo) : NaN;
      const platform = 'platform' in item && typeof item.platform === 'string' ? item.platform : '';
      const verified = 'verified' in item ? Boolean(item.verified) : true;
      const rawType = 'type' in item && typeof item.type === 'string' ? item.type : '';
      const inferredType = rawType === 'review' ? 'review' : 'purchase';

      if (!name || !platform || !Number.isFinite(minutesAgo)) {
        return null;
      }

      if (inferredType === 'review') {
        const rating = 'rating' in item ? Number(item.rating) : NaN;
        if (!Number.isFinite(rating)) {
          return null;
        }
        return {
          type: 'review',
          name,
          minutesAgo,
          platform,
          rating,
          verified,
        };
      }

      const boxes = 'boxes' in item ? Number(item.boxes) : NaN;
      if (!Number.isFinite(boxes)) {
        return null;
      }
      return {
        type: 'purchase',
        name,
        minutesAgo,
        platform,
        boxes,
        verified,
      };
    })
    .filter((item): item is SocialProofEvent => item !== null);
}

export default function HomePage() {
  const t = useTranslations('Index');
  const socialProofT = useTranslations('Index.marketing.socialProof');
  const locale = useLocale();
  const [selectedProduct, setSelectedProduct] = useState<DisplayProduct | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [products, setProducts] = useState<DisplayProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const addItem = useCartStore((state) => state.addItem);

  const socialProofEvents = useMemo(
    () => parseSocialProofEvents(socialProofT.raw('events')),
    [socialProofT],
  );

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
      <NlpMiddleStorySection />
      <TrustStatsStrip />
      <UGCPhotoTicker />
      <AuthorityPartnerSection />
      <ShippingCountdownSection />
      <UGCReviewGrid />
      <TargetAudienceSection />
      <ScienceEndorsementSection />
      <NlpPriceReframeSection />
      <ProductPricingSection
        products={products}
        isLoading={isLoading}
        onAddToCart={handleAddToCart}
        onBuyNow={handleBuyNow}
      />
      <NlpTakeawaySection />
      <Footer />
      <MobileFloatingCTA />
      <SocialProofToast events={socialProofEvents} />
      <CheckoutModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        product={selectedProduct}
      />
    </main>
  );
}
