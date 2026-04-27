"use client";

import { useTranslations } from "next-intl";
import { ProductCard } from "./ProductCard";
import type { DisplayProduct } from "@/lib/product-service";

interface ProductPricingSectionProps {
  products: DisplayProduct[];
  isLoading: boolean;
  onBuyNow: (product: DisplayProduct) => void;
}

export default function ProductPricingSection({
  products,
  isLoading,
  onBuyNow,
}: ProductPricingSectionProps) {
  const t = useTranslations("Index");

  return (
    <section className="w-full py-24 px-6 sm:px-12 bg-white" id="products">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold text-charcoal">
            {t("products.title")}
          </h2>
          <p className="text-charcoal/60 max-w-2xl mx-auto">
            {t("products.subtitle")}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {isLoading
            ? // Loading skeleton
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="bg-ivory rounded-3xl aspect-square mb-4"></div>
                  <div className="h-4 bg-charcoal/20 rounded mb-2"></div>
                  <div className="h-8 bg-charcoal/20 rounded mb-4"></div>
                  <div className="h-12 bg-charcoal/10 rounded"></div>
                </div>
              ))
            : products.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onBuyNow={onBuyNow}
                />
              ))}
        </div>
      </div>
    </section>
  );
}
