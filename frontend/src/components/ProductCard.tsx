"use client";

import { useTranslations } from "next-intl";
import Image from "next/image";
import { CheckCircle2, QrCode } from "lucide-react";
import { useEffect, useRef } from "react";
import { IMAGES } from "@/lib/image-utils";
import { trackLandingFunnelEvent } from "@/lib/marketing-analytics";
import {
  resolveFixedPackKeyByMeta,
  resolveFixedProductImageByMeta,
  type DisplayProduct,
} from "@/lib/product-display";

interface ProductCardProps {
  product: DisplayProduct;
  onBuyNow: (product: DisplayProduct) => void;
  priority?: boolean;
  conversionLayout?: boolean;
  viewTrackingSource?: string;
}

const optimizedProductImages: Record<string, string> = {
  pack1: IMAGES.products.box1,
  pack2: IMAGES.products.box2,
  pack4: IMAGES.products.box4,
  pack6: IMAGES.products.box6,
};

export function ProductCard({
  product,
  onBuyNow,
  priority = false,
  conversionLayout = false,
  viewTrackingSource,
}: ProductCardProps) {
  const t = useTranslations("Index");
  const cardRef = useRef<HTMLElement | null>(null);
  const hasTrackedViewRef = useRef(false);
  const packKey = resolveFixedPackKeyByMeta({
    id: product.id,
    packSize: product.label,
    nameEn: product.name,
    nameZh: product.name,
    price: product.price,
  });
  const rawFeatures = t.raw(`products.details.${packKey}`);
  const features = Array.isArray(rawFeatures)
    ? rawFeatures
    : [product.label, t("products.detailFallbackOne"), t("products.detailFallbackTwo")];
  const freeShippingEligible = Number(product.price) >= 70;
  const cardImage =
    optimizedProductImages[packKey] ??
    resolveFixedProductImageByMeta({
      id: product.id,
      packSize: product.label,
      nameEn: product.name,
      nameZh: product.name,
      price: product.price,
    });

  useEffect(() => {
    const element = cardRef.current;
    if (!element || hasTrackedViewRef.current || !viewTrackingSource) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting || hasTrackedViewRef.current) return;

        hasTrackedViewRef.current = true;
        trackLandingFunnelEvent("product_card_view", {
          source: viewTrackingSource,
          product_id: product.id,
          product_name: product.name,
          product_value: Number(product.price),
        });
        observer.disconnect();
      },
      { threshold: 0.5 },
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [product.id, product.name, product.price, viewTrackingSource]);

  const imageFrameClassName = conversionLayout
    ? "premium-outline relative mb-4 mt-6 h-40 overflow-hidden rounded-[1.2rem] bg-[radial-gradient(circle_at_top,rgba(255,184,0,0.16),transparent_36%),linear-gradient(180deg,rgba(17,43,34,0.6),rgba(9,26,20,0.9))] sm:mb-5 sm:h-52 xl:h-48"
    : "premium-outline relative mb-5 mt-6 aspect-[4/5] overflow-hidden rounded-[1.2rem] bg-[radial-gradient(circle_at_top,rgba(255,184,0,0.16),transparent_36%),linear-gradient(180deg,rgba(17,43,34,0.6),rgba(9,26,20,0.9))]";

  const buyButton = (
    <button
      id={`product-buy-now-${product.id}`}
      type="button"
      onClick={() => onBuyNow(product)}
      className="gold-button inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-md px-4 text-sm font-bold uppercase tracking-[0.18em]"
    >
      <QrCode size={16} />
      <span>{t("products.buyNow")}</span>
    </button>
  );

  const featureList = (
    <ul
      className={[
        "flex-1 space-y-2 border-t border-primary/14 pt-5",
        conversionLayout ? "mt-5" : "mb-6",
      ].join(" ")}
    >
      {features.slice(0, 3).map((feature) => (
        <li key={feature} className="flex items-start gap-3 text-sm leading-6 text-text-light/80">
          <CheckCircle2 size={18} className="mt-1 shrink-0 text-primary" />
          <span>{feature}</span>
        </li>
      ))}
    </ul>
  );

  return (
    <article
      ref={cardRef}
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

      <div className={imageFrameClassName}>
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

      <div className="mb-4 space-y-3">
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

      {conversionLayout ? (
        <>
          {buyButton}
          {featureList}
        </>
      ) : (
        <>
          {featureList}
          {buyButton}
        </>
      )}
    </article>
  );
}
