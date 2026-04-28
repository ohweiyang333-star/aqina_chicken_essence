"use client";

import Image from "next/image";
import { ArrowRight, CheckCircle2, Crown, Sparkles } from "lucide-react";
import { useTranslations } from "next-intl";
import type { DisplayProduct } from "@/lib/product-service";
import { resolveFixedPackKeyByMeta } from "@/lib/product-service";

interface V3OfferSectionProps {
  products: DisplayProduct[];
  isLoading: boolean;
  onBuyNow: (product: DisplayProduct) => void;
}

interface OfferCopy {
  packKey: "pack1" | "pack4";
  eyebrow: string;
  title: string;
  subtitle: string;
  originalPrice?: string;
  badge?: string;
  cta: string;
  features: string[];
}

function getPackKey(product: DisplayProduct) {
  return resolveFixedPackKeyByMeta({
    id: product.id,
    packSize: product.label,
    nameEn: product.name,
    nameZh: product.name,
    price: product.price,
  });
}

export default function V3OfferSection({
  products,
  isLoading,
  onBuyNow,
}: V3OfferSectionProps) {
  const t = useTranslations("Index.v3.offer");
  const offerItems = t.raw("items") as OfferCopy[];
  const displayProducts = offerItems
    .map((item) => ({
      copy: item,
      product: products.find((product) => getPackKey(product) === item.packKey),
    }))
    .filter((item): item is { copy: OfferCopy; product: DisplayProduct } =>
      Boolean(item.product),
    );

  return (
    <section
      id="products"
      className="relative scroll-mt-24 bg-[#f7eddc] py-16 text-[#2f2418] md:py-24"
    >
      <div className="absolute inset-x-0 top-0 h-px bg-[#c99744]/45" />
      <div className="section-shell space-y-10">
        <div className="mx-auto max-w-3xl space-y-4 text-center">
          <p className="text-xs font-bold uppercase text-[#8b6f38]">
            {t("eyebrow")}
          </p>
          <h2 className="font-heading text-4xl font-semibold leading-tight text-[#2f2418] md:text-5xl">
            {t("title")}
          </h2>
          <p className="text-base leading-8 text-[#725f4d] md:text-lg">
            {t("body")}
          </p>
        </div>

        {isLoading ? (
          <div className="grid gap-5 md:grid-cols-2">
            {Array.from({ length: 2 }).map((_, index) => (
              <div
                key={index}
                className="min-h-[32rem] animate-pulse rounded-lg border border-[#d8c5a6] bg-white/70 p-5"
              >
                <div className="mb-5 aspect-[4/3] rounded-lg bg-[#dcc9aa]" />
                <div className="mb-3 h-5 rounded bg-[#dcc9aa]" />
                <div className="mb-6 h-10 rounded bg-[#dcc9aa]" />
                <div className="space-y-3">
                  <div className="h-4 rounded bg-[#dcc9aa]" />
                  <div className="h-4 rounded bg-[#dcc9aa]" />
                  <div className="h-4 rounded bg-[#dcc9aa]" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid gap-5 lg:grid-cols-[0.92fr_1.08fr]">
            {displayProducts.map(({ copy, product }) => {
              const isPopular = copy.packKey === "pack4";
              const freeShipping = Number(product.price) >= 70;

              return (
                <article
                  key={copy.packKey}
                  className={[
                    "relative flex h-full flex-col overflow-hidden rounded-lg border bg-[#fffaf1] p-5 shadow-[0_22px_60px_rgba(103,70,28,0.12)]",
                    isPopular
                      ? "border-[#b9852e] lg:-mt-4 lg:mb-4"
                      : "border-[#dfcfb7]",
                  ].join(" ")}
                >
                  {copy.badge ? (
                    <div className="absolute right-4 top-4 z-10 inline-flex items-center gap-2 rounded-full bg-[#2f5c46] px-3 py-2 text-xs font-bold text-[#fffaf1]">
                      <Crown size={14} />
                      <span>{copy.badge}</span>
                    </div>
                  ) : null}

                  <div className="relative mb-6 aspect-[4/3] overflow-hidden rounded-lg bg-[radial-gradient(circle_at_20%_10%,rgba(209,151,54,0.2),transparent_32%),linear-gradient(135deg,#fff7e8,#e8dbc3)]">
                    <Image
                      src={product.image}
                      alt={copy.title}
                      fill
                      sizes="(max-width: 768px) 92vw, 44vw"
                      className="object-contain p-7"
                    />
                  </div>

                  <div className="mb-6 space-y-4">
                    <div className="space-y-2">
                      <p className="text-xs font-bold uppercase text-[#9a7336]">
                        {copy.eyebrow}
                      </p>
                      <h3 className="font-heading text-4xl font-semibold leading-tight text-[#2f2418]">
                        {copy.title}
                      </h3>
                      <p className="text-sm leading-7 text-[#725f4d]">
                        {copy.subtitle}
                      </p>
                    </div>

                    <div className="flex flex-wrap items-end gap-3">
                      <span className="text-xs font-bold uppercase text-[#9a7336]">
                        SGD
                      </span>
                      <span className="font-heading text-6xl font-semibold leading-none text-[#2f2418]">
                        {Number(product.price).toFixed(2)}
                      </span>
                      {copy.originalPrice ? (
                        <span className="pb-2 text-sm font-bold text-[#9d8a72] line-through">
                          {copy.originalPrice}
                        </span>
                      ) : null}
                    </div>

                    {freeShipping ? (
                      <span className="inline-flex items-center rounded-full border border-[#7f9c7b]/45 bg-[#e8f0e4] px-3 py-2 text-xs font-bold text-[#2f5c46]">
                        {t("freeShipping")}
                      </span>
                    ) : null}
                  </div>

                  <ul className="mb-6 flex-1 space-y-3 border-t border-[#d9c6a9] pt-5">
                    {copy.features.map((feature) => (
                      <li
                        key={feature}
                        className="flex items-start gap-3 text-sm leading-7 text-[#5d4b3c]"
                      >
                        <CheckCircle2
                          size={18}
                          className="mt-1 shrink-0 text-[#b9852e]"
                        />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <button
                    id={`v3-offer-${copy.packKey}-cta`}
                    type="button"
                    onClick={() => onBuyNow(product)}
                    className={[
                      "inline-flex min-h-14 w-full items-center justify-center gap-2 rounded-lg px-5 text-sm font-bold",
                      isPopular
                        ? "bg-[#2f2418] text-[#fffaf1] shadow-[0_16px_34px_rgba(47,36,24,0.24)] hover:bg-[#8b6122]"
                        : "border border-[#b9852e] bg-white text-[#6f4b1d] hover:bg-[#fff5e2]",
                    ].join(" ")}
                  >
                    {isPopular ? <Sparkles size={17} /> : <ArrowRight size={17} />}
                    <span>{copy.cta}</span>
                  </button>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
