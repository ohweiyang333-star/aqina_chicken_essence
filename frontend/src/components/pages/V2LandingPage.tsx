'use client';

import dynamic from 'next/dynamic';
import Footer from '@/components/Footer';
import MobileFloatingCTA from '@/components/MobileFloatingCTA';
import MediaLoadGate from '@/components/MediaLoadGate';
import ProductPricingSection from '@/components/ProductPricingSection';
import V2BofuOrderSection from '@/components/v2/V2BofuOrderSection';
import V2ComparisonSection from '@/components/v2/V2ComparisonSection';
import V2CraftLightnessSection from '@/components/v2/V2CraftLightnessSection';
import V2HeroSection from '@/components/v2/V2HeroSection';
import V2PineappleStorySection from '@/components/v2/V2PineappleStorySection';
import V2ProductPricingBand from '@/components/v2/V2ProductPricingBand';
import V2QuickTrustStrip from '@/components/v2/V2QuickTrustStrip';
import useLandingProducts from '@/hooks/useLandingProducts';
import { trackLandingFunnelEvent } from '@/lib/marketing-analytics';
import type { DisplayProduct } from '@/lib/product-display';
import { useLocale, useTranslations } from 'next-intl';

const CheckoutModal = dynamic(() => import('@/components/CheckoutModal'), {
  ssr: false,
});
const V2AudienceSection = dynamic(() => import('@/components/v2/V2AudienceSection'));
const V2FAQSection = dynamic(() => import('@/components/v2/V2FAQSection'));
const V2FinalCtaSection = dynamic(() => import('@/components/v2/V2FinalCtaSection'));
const V2TrustSection = dynamic(() => import('@/components/v2/V2TrustSection'));
const V2UgcEvidenceWall = dynamic(() => import('@/components/v2/V2UgcEvidenceWall'));

export default function V2LandingPage() {
  const t = useTranslations('Index');
  const locale = useLocale();
  const {
    products,
    isLoading,
    selectedProduct,
    isCheckoutOpen,
    handleBuyNow,
    closeCheckout,
  } = useLandingProducts({ useStaticProducts: true });

  const handleV2BuyNow = (product: DisplayProduct) => {
    trackLandingFunnelEvent('product_buy_click', {
      source: 'v2_product_card',
      product_id: product.id,
      product_name: product.name,
      product_value: Number(product.price),
    });
    trackLandingFunnelEvent('checkout_open', {
      source: 'v2_product_card',
      product_id: product.id,
      product_name: product.name,
      product_value: Number(product.price),
    });
    handleBuyNow(product);
  };

  return (
    <MediaLoadGate
      cacheKey={`aqina-v2-landing-media-v3-${locale}`}
      sources={[]}
      blocking={false}
      variant="warm"
      loadingLabel={t('loading.mediaPreparing')}
    >
      <main className="flex min-h-screen flex-col bg-[#fff7e8] pb-24 text-[#23170d]">
        <V2HeroSection />
        <V2ProductPricingBand>
          <ProductPricingSection
            products={products}
            isLoading={isLoading}
            onBuyNow={handleV2BuyNow}
            priorityImageCount={0}
            conversionLayout
            showWhatsAppFallback
          />
        </V2ProductPricingBand>
        <V2BofuOrderSection />
        <V2QuickTrustStrip />
        <V2FAQSection />
        <V2ComparisonSection />
        <V2PineappleStorySection />
        <V2CraftLightnessSection />
        <V2AudienceSection />
        <V2UgcEvidenceWall />
        <V2TrustSection />
        <V2FinalCtaSection />
        <Footer />
        {!isCheckoutOpen ? <MobileFloatingCTA /> : null}
        {isCheckoutOpen || selectedProduct ? (
          <CheckoutModal
            isOpen={isCheckoutOpen}
            onClose={closeCheckout}
            product={selectedProduct}
          />
        ) : null}
      </main>
    </MediaLoadGate>
  );
}
