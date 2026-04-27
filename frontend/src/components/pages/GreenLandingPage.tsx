'use client';

import AuthorityPartnerSection from '@/components/AuthorityPartnerSection';
import CheckoutModal from '@/components/CheckoutModal';
import Footer from '@/components/Footer';
import HeroFlashSection from '@/components/HeroFlashSection';
import MobileFloatingCTA from '@/components/MobileFloatingCTA';
import ProductPricingSection from '@/components/ProductPricingSection';
import PromoMarquee from '@/components/PromoMarquee';
import SocialProofToast from '@/components/SocialProofToast';
import StoryExperienceSection from '@/components/StoryExperienceSection';
import UGCReviewGrid from '@/components/UGCReviewGrid';
import useLandingProducts from '@/hooks/useLandingProducts';

export default function GreenLandingPage() {
  const {
    products,
    isLoading,
    selectedProduct,
    isCheckoutOpen,
    handleBuyNow,
    handleAddToCart,
    closeCheckout,
  } = useLandingProducts();

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
        isOpen={isCheckoutOpen}
        onClose={closeCheckout}
        product={selectedProduct}
      />
    </main>
  );
}
