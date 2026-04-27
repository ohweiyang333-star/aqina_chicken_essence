'use client';

import AuthorityPartnerSection from '@/components/AuthorityPartnerSection';
import CheckoutModal from '@/components/CheckoutModal';
import Footer from '@/components/Footer';
import HeroFlashSection from '@/components/HeroFlashSection';
import MobileFloatingCTA from '@/components/MobileFloatingCTA';
import MediaLoadGate from '@/components/MediaLoadGate';
import ProductPricingSection from '@/components/ProductPricingSection';
import PromoMarquee from '@/components/PromoMarquee';
import SocialProofToast from '@/components/SocialProofToast';
import StoryExperienceSection from '@/components/StoryExperienceSection';
import UGCReviewGrid from '@/components/UGCReviewGrid';
import useLandingProducts from '@/hooks/useLandingProducts';
import { greenLandingMedia } from '@/lib/landing-media';

export default function GreenLandingPage() {
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
      cacheKey="aqina-green-landing-media-v3"
      sources={greenLandingMedia}
      variant="dark"
    >
      <main className="page-grid flex min-h-screen flex-col pb-24">
        <PromoMarquee />
        <HeroFlashSection />
        <StoryExperienceSection />
        <UGCReviewGrid />
        <AuthorityPartnerSection />
        <ProductPricingSection
          products={products}
          isLoading={isLoading}
          onBuyNow={handleBuyNow}
        />
        <Footer />
        <SocialProofToast />
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
