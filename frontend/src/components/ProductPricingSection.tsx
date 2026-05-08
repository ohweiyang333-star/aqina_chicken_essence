"use client";

import { useTranslations } from "next-intl";
import { MessageCircle } from "lucide-react";
import { ProductCard } from "./ProductCard";
import type { DisplayProduct } from "@/lib/product-display";
import { getWhatsAppHref } from "@/lib/site-config";
import { trackLandingFunnelEvent } from "@/lib/marketing-analytics";

interface ProductPricingSectionProps {
  products: DisplayProduct[];
  isLoading: boolean;
  onBuyNow: (product: DisplayProduct) => void;
  priorityImageCount?: number;
  conversionLayout?: boolean;
  showWhatsAppFallback?: boolean;
}

export default function ProductPricingSection({
  products,
  isLoading,
  onBuyNow,
  priorityImageCount = 2,
  conversionLayout = false,
  showWhatsAppFallback = false,
}: ProductPricingSectionProps) {
  const t = useTranslations("Index");

  return (
    <section className="relative scroll-mt-24 py-20 md:py-24" id="products">
      <div className="section-shell space-y-10">
        <div className="space-y-4 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.34em] text-primary">
            {t("products.eyebrow")}
          </p>
          <h2 className="font-heading text-4xl font-semibold text-text-light md:text-5xl">
            {t("products.title")}
          </h2>
          <p className="mx-auto max-w-2xl text-sm leading-7 text-muted md:text-base">
            {t("products.subtitle")}
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
          {isLoading
            ? Array.from({ length: 4 }).map((_, index) => (
                <div
                  key={index}
                  className="surface-panel animate-pulse rounded-2xl p-5"
                >
                  <div className="mb-5 aspect-[4/5] rounded-xl bg-primary/8" />
                  <div className="mb-3 h-5 rounded bg-primary/10" />
                  <div className="mb-5 h-4 w-2/3 rounded bg-primary/8" />
                  <div className="mb-3 h-10 rounded bg-primary/8" />
                  <div className="space-y-2">
                    <div className="h-3 rounded bg-primary/8" />
                    <div className="h-3 rounded bg-primary/8" />
                    <div className="h-3 rounded bg-primary/8" />
                  </div>
                </div>
              ))
            : products.map((product, index) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onBuyNow={onBuyNow}
                  priority={index < priorityImageCount}
                  conversionLayout={conversionLayout}
                  viewTrackingSource={conversionLayout ? "v2_product_card" : undefined}
                />
              ))}
        </div>

        {showWhatsAppFallback && (
          <div className="mx-auto max-w-3xl rounded-2xl border border-primary/22 bg-background-dark/78 p-5 text-center shadow-[0_16px_46px_rgba(0,0,0,0.28)] md:p-6">
            <p className="font-heading text-2xl font-semibold text-text-light">
              {t("products.whatsappFallbackTitle")}
            </p>
            <p className="mx-auto mt-2 max-w-2xl text-sm leading-7 text-muted">
              {t("products.whatsappFallbackBody")}
            </p>
            <a
              id="v2-product-whatsapp-fallback"
              href={getWhatsAppHref(t("products.whatsappMessage"))}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => {
                trackLandingFunnelEvent("whatsapp_cta_click", {
                  source: "v2_product_whatsapp_fallback",
                  destination: "whatsapp",
                });
              }}
              className="mt-4 inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-primary/35 bg-white/8 px-5 text-sm font-bold text-text-light transition hover:-translate-y-0.5 hover:border-primary hover:bg-primary/12"
            >
              <MessageCircle size={17} />
              <span>{t("products.whatsappFallbackCta")}</span>
            </a>
          </div>
        )}
      </div>
    </section>
  );
}
