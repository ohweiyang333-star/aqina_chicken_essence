"use client";

import CheckoutModal from "@/components/CheckoutModal";
import Footer from "@/components/Footer";
import MediaLoadGate from "@/components/MediaLoadGate";
import MobileFloatingCTA from "@/components/MobileFloatingCTA";
import V3OfferSection from "@/components/v3/V3OfferSection";
import {
  V3CertificationsSection,
  V3EmpathySection,
  V3FinalCtaSection,
  V3HeroSection,
  V3SolutionSection,
  V3StoriesSection,
} from "@/components/v3/V3MaternitySections";
import useLandingProducts from "@/hooks/useLandingProducts";
import { v3MaternityLandingMedia } from "@/lib/landing-media";
import { useTranslations } from "next-intl";

export default function V3MaternityLandingPage() {
  const t = useTranslations("Index");
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
      cacheKey="aqina-v3-maternity-media-v1"
      sources={v3MaternityLandingMedia}
      variant="warm"
      loadingLabel={t("loading.mediaPreparing")}
    >
      <main className="flex min-h-screen flex-col bg-[#f7eddc] pb-24 text-[#2f2418]">
        <V3HeroSection />
        <V3EmpathySection />
        <V3SolutionSection />
        <V3CertificationsSection />
        <V3StoriesSection />
        <V3OfferSection
          products={products}
          isLoading={isLoading}
          onBuyNow={handleBuyNow}
        />
        <V3FinalCtaSection />
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
