"use client";

import { useTranslations } from "next-intl";
import { ProductCard } from "./ProductCard";
import type { DisplayProduct } from "@/lib/product-service";

interface ProductPricingSectionProps {
  products: DisplayProduct[];
  isLoading: boolean;
  onAddToCart: (product: DisplayProduct) => void;
  onBuyNow: (product: DisplayProduct) => void;
}

export default function ProductPricingSection({
  products,
  isLoading,
  onAddToCart,
  onBuyNow,
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
            : products.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onAddToCart={onAddToCart}
                  onBuyNow={onBuyNow}
                />
              ))}
        </div>
      </div>
    </section>
  );
}
