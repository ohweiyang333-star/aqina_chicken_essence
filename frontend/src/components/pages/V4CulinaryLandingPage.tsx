"use client";

import CheckoutModal from "@/components/CheckoutModal";
import Footer from "@/components/Footer";
import MediaLoadGate from "@/components/MediaLoadGate";
import MobileFloatingCTA from "@/components/MobileFloatingCTA";
import {
  V4FinalCtaSection,
  V4FrustrationSection,
  V4HeroSection,
  V4OfferSection,
  V4ShowcaseSection,
  V4SuperioritySection,
} from "@/components/v4/V4CulinarySections";
import useLandingProducts from "@/hooks/useLandingProducts";
import { v4CulinaryLandingMedia } from "@/lib/landing-media";
import {
  v4CulinaryContent,
  type V4Locale,
} from "@/lib/v4-culinary-content";

interface V4CulinaryLandingPageProps {
  locale: V4Locale;
}

export default function V4CulinaryLandingPage({
  locale,
}: V4CulinaryLandingPageProps) {
  const content = v4CulinaryContent[locale];
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
      cacheKey={`aqina-v4-culinary-media-v4-${locale}`}
      sources={v4CulinaryLandingMedia}
      variant="dark"
      loadingLabel={content.loadingLabel}
    >
      <main className="flex min-h-screen flex-col bg-[#080706] pb-24 text-[#fff8e8]">
        <V4HeroSection content={content} />
        <V4FrustrationSection content={content} />
        <V4ShowcaseSection content={content} />
        <V4SuperioritySection content={content} />
        <V4OfferSection
          content={content}
          products={products}
          isLoading={isLoading}
          onBuyNow={handleBuyNow}
        />
        <V4FinalCtaSection content={content} />
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
