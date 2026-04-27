'use client';

import CheckoutModal from '@/components/CheckoutModal';
import Footer from '@/components/Footer';
import MobileFloatingCTA from '@/components/MobileFloatingCTA';
import MediaLoadGate from '@/components/MediaLoadGate';
import ProductPricingSection from '@/components/ProductPricingSection';
import V2AudienceSection from '@/components/v2/V2AudienceSection';
import V2ComparisonSection from '@/components/v2/V2ComparisonSection';
import V2CraftLightnessSection from '@/components/v2/V2CraftLightnessSection';
import V2FinalCtaSection from '@/components/v2/V2FinalCtaSection';
import V2HeroSection from '@/components/v2/V2HeroSection';
import V2PineappleStorySection from '@/components/v2/V2PineappleStorySection';
import V2ProductPricingBand from '@/components/v2/V2ProductPricingBand';
import V2TrustSection from '@/components/v2/V2TrustSection';
import V2UgcEvidenceWall from '@/components/v2/V2UgcEvidenceWall';
import useLandingProducts from '@/hooks/useLandingProducts';
import { v2LandingMedia } from '@/lib/landing-media';

export default function V2LandingPage() {
  const {
    products,
    isLoading,
    selectedProduct,
    isCheckoutOpen,
    handleBuyNow,
    closeCheckout,
  } = useLandingProducts();

  return (
    <MediaLoadGate
      cacheKey="aqina-v2-landing-media-v3"
      sources={v2LandingMedia}
      variant="warm"
    >
      <main className="flex min-h-screen flex-col bg-[#fff7e8] pb-24 text-[#23170d]">
        <V2HeroSection />
        <V2ComparisonSection />
        <V2PineappleStorySection />
        <V2CraftLightnessSection />
        <V2AudienceSection />
        <V2TrustSection />
        <V2UgcEvidenceWall />
        <V2ProductPricingBand>
          <ProductPricingSection
            products={products}
            isLoading={isLoading}
            onBuyNow={handleBuyNow}
          />
        </V2ProductPricingBand>
        <V2FinalCtaSection />
        <Footer />
        <MobileFloatingCTA />
        <CheckoutModal
          isOpen={isCheckoutOpen}
          onClose={closeCheckout}
          product={selectedProduct}
        />
      </main>
    </MediaLoadGate>
  );
}
