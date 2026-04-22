"use client";

import { useTranslations } from "next-intl";
import Image from "next/image";
import { CheckCircle2, Plus, ShoppingCart } from "lucide-react";
import type { DisplayProduct } from "@/lib/product-service";
import { resolveFixedProductImageByMeta } from "@/lib/product-service";

interface ProductCardProps {
  product: DisplayProduct;
  onAddToCart: (product: DisplayProduct) => void;
  onBuyNow: (product: DisplayProduct) => void;
  priority?: boolean;
}

const optimizedProductImages: Record<string, string> = {
  pack1: '/images/pack-1.webp',
  pack2: '/images/pack-2.webp',
  pack4: '/images/pack-4.webp',
  pack6: '/images/pack-6.webp',
};

export function ProductCard({
  product,
  onAddToCart,
  onBuyNow,
  priority = false,
}: ProductCardProps) {
  const t = useTranslations("Index");
  const rawFeatures = t.raw(`products.details.${product.id}`);
  const features = Array.isArray(rawFeatures)
    ? rawFeatures
    : [product.label, t("products.detailFallbackOne"), t("products.detailFallbackTwo")];
  const freeShippingEligible = Number(product.price) >= 70;
  const cardImage =
    optimizedProductImages[product.id] ??
    resolveFixedProductImageByMeta({
      id: product.id,
      packSize: product.label,
      nameEn: product.name,
      nameZh: product.name,
      price: product.price,
    });

  return (
    <article
      className={[
        "surface-panel relative flex h-full flex-col overflow-hidden rounded-[1.4rem] p-5",
        product.popular
          ? "border-primary/40 shadow-[0_24px_70px_rgba(0,0,0,0.4)] md:-translate-y-3"
          : "",
      ].join(" ")}
    >
      {product.popular && (
        <div className="absolute left-5 top-5 z-20 rounded-full bg-primary px-3 py-1 text-[10px] font-bold uppercase tracking-[0.28em] text-background-dark">
          {t("products.recommended")}
        </div>
      )}

      <div className="premium-outline relative mb-5 mt-6 aspect-[4/5] overflow-hidden rounded-[1.2rem] bg-[radial-gradient(circle_at_top,rgba(255,184,0,0.16),transparent_36%),linear-gradient(180deg,rgba(17,43,34,0.6),rgba(9,26,20,0.9))]">
        <Image
          src={cardImage}
          alt={product.name}
          fill
          priority={priority}
          loading={priority ? "eager" : "lazy"}
          className="object-contain p-6"
          sizes="(max-width: 768px) 100vw, (max-width: 1280px) 50vw, 25vw"
        />
      </div>

      <div className="mb-5 space-y-3">
        <div className="space-y-1">
          <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-primary">
            {product.badge || product.label}
          </p>
          <h3 className="font-heading text-[2rem] leading-none font-semibold text-text-light">
            {product.name}
          </h3>
          <p className="text-sm text-muted">{product.label}</p>
        </div>

        <div className="flex items-end gap-2">
          <span className="text-sm font-bold uppercase tracking-[0.2em] text-primary">
            {t("products.currency")}
          </span>
          <span className="font-heading text-5xl leading-none font-semibold text-text-light">
            {Number(product.price).toFixed(2)}
          </span>
        </div>
        {freeShippingEligible && (
          <span className="inline-flex items-center rounded-full border border-emerald-400/40 bg-emerald-500/15 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-200">
            {t("products.freeShippingBadge")}
          </span>
        )}
      </div>

      <ul className="mb-6 flex-1 space-y-2 border-t border-primary/14 pt-5">
        {features.slice(0, 3).map((feature) => (
          <li key={feature} className="flex items-start gap-3 text-sm leading-6 text-text-light/80">
            <CheckCircle2 size={18} className="mt-1 shrink-0 text-primary" />
            <span>{feature}</span>
          </li>
        ))}
      </ul>

      <div className="space-y-3">
        <button
          id={`product-buy-now-${product.id}`}
          type="button"
          onClick={() => onBuyNow(product)}
          className="gold-button inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-md px-4 text-sm font-bold uppercase tracking-[0.18em]"
        >
          <ShoppingCart size={16} />
          <span>{t("products.buyNow")}</span>
        </button>
        <button
          id={`product-add-cart-${product.id}`}
          type="button"
          onClick={() => onAddToCart(product)}
          className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-md border border-primary/22 bg-background-dark/55 px-4 text-sm font-semibold uppercase tracking-[0.16em] text-text-light hover:border-primary/45 hover:text-primary"
        >
          <Plus size={16} />
          <span>{t("products.addToCart")}</span>
        </button>
      </div>
    </article>
  );
}
