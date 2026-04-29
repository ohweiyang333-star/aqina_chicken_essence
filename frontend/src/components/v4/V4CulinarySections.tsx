"use client";

import Image from "next/image";
import {
  ArrowRight,
  BadgeCheck,
  ChefHat,
  CheckCircle2,
  Clock3,
  Crown,
  Droplets,
  Flame,
  HeartPulse,
  MessageCircle,
  Package,
  ShieldCheck,
  Soup,
  Sparkles,
} from "lucide-react";
import {
  motion,
  useReducedMotion,
  useScroll,
  useTransform,
} from "framer-motion";
import type { ReactNode } from "react";

import { IMAGES } from "@/lib/image-utils";
import { getWhatsAppHref } from "@/lib/site-config";
import type {
  V4PackKey,
  V4RecipeIcon,
  V4SuperiorityIcon,
} from "@/lib/v4-culinary-content";
import { v4CulinaryContent, v4Media } from "@/lib/v4-culinary-content";
import type { DisplayProduct } from "@/lib/product-service";
import { resolveFixedPackKeyByMeta } from "@/lib/product-service";

type V4Content = (typeof v4CulinaryContent)[keyof typeof v4CulinaryContent];

interface V4SectionProps {
  content: V4Content;
}

interface V4OfferSectionProps extends V4SectionProps {
  products: DisplayProduct[];
  isLoading: boolean;
  onBuyNow: (product: DisplayProduct) => void;
}

const recipeIcons: Record<V4RecipeIcon, typeof Clock3> = {
  clock: Clock3,
  heart: HeartPulse,
  flame: Flame,
};

const superiorityIcons: Record<V4SuperiorityIcon, typeof ChefHat> = {
  taste: ChefHat,
  purity: Droplets,
  light: ShieldCheck,
};

const productImagesByPack: Record<V4PackKey, string> = {
  pack1: IMAGES.products.box1,
  pack2: IMAGES.products.box2,
  pack4: IMAGES.products.box4,
  pack6: IMAGES.products.box6,
};

function getPackKey(product: DisplayProduct) {
  return resolveFixedPackKeyByMeta({
    id: product.id,
    packSize: product.label,
    nameEn: product.name,
    nameZh: product.name,
    price: product.price,
  });
}

function Reveal({
  children,
  className = "",
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 22 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.72, ease: [0.22, 1, 0.36, 1], delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <p className="text-xs font-bold uppercase tracking-[0.24em] text-[#d8a943]">
      {children}
    </p>
  );
}

export function V4HeroSection({ content }: V4SectionProps) {
  const shouldReduceMotion = useReducedMotion();
  const { scrollY } = useScroll();
  const imageY = useTransform(scrollY, [0, 900], [0, 120]);
  const copyY = useTransform(scrollY, [0, 900], [0, -48]);

  return (
    <section
      id="v4-hero"
      className="relative isolate min-h-[calc(100vh-4rem)] overflow-hidden bg-[#080706] text-[#fff8e8]"
    >
      <motion.div
        aria-hidden="true"
        className="absolute inset-0 -z-30"
        style={shouldReduceMotion ? undefined : { y: imageY }}
      >
        <Image
          src={v4Media.hero}
          alt={content.hero.imageAlt}
          fill
          priority
          sizes="100vw"
          className="object-cover object-[52%_center]"
        />
      </motion.div>
      <div className="absolute inset-0 -z-20 bg-[linear-gradient(90deg,rgba(8,7,6,0.96)_0%,rgba(8,7,6,0.82)_35%,rgba(8,7,6,0.34)_64%,rgba(8,7,6,0.2)_100%)]" />
      <div className="absolute inset-0 -z-10 bg-[linear-gradient(180deg,rgba(8,7,6,0.18)_0%,rgba(8,7,6,0.18)_64%,#080706_100%)]" />

      <div className="section-shell grid min-h-[calc(100vh-4rem)] items-center gap-10 pb-16 pt-28 lg:grid-cols-[0.94fr_1.06fr]">
        <motion.div
          className="max-w-3xl space-y-7"
          style={shouldReduceMotion ? undefined : { y: copyY }}
        >
          <Reveal>
            <div className="inline-flex items-center gap-2 rounded-lg border border-[#d8a943]/38 bg-[#17110a]/72 px-4 py-2 text-xs font-bold uppercase tracking-[0.18em] text-[#f4c65b] shadow-[0_16px_42px_rgba(0,0,0,0.28)] backdrop-blur">
              <Sparkles size={15} />
              <span>{content.hero.eyebrow}</span>
            </div>
          </Reveal>

          <Reveal delay={0.08} className="space-y-5">
            <h1 className="font-heading text-5xl font-semibold leading-[1.02] text-[#fff8e8] md:text-7xl">
              {content.hero.title}
            </h1>
            <p className="max-w-2xl text-base leading-8 text-[#f2d9ae]/86 md:text-xl">
              {content.hero.subtitle}
            </p>
          </Reveal>

          <Reveal delay={0.16} className="flex flex-col gap-3 sm:flex-row">
            <a
              id="v4-hero-whatsapp-cta"
              href={getWhatsAppHref(content.finalCta.whatsappMessage)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg bg-[#f2b53d] px-6 text-sm font-black uppercase tracking-[0.12em] text-[#130d06] shadow-[0_18px_44px_rgba(242,181,61,0.28)] hover:bg-[#ffd46d] hover:shadow-[0_22px_58px_rgba(242,181,61,0.42)]"
            >
              <MessageCircle size={17} />
              <span>{content.hero.cta}</span>
            </a>
            <a
              id="v4-hero-products-cta"
              href="#products"
              className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg border border-[#e1bd70]/50 bg-[#17110a]/72 px-6 text-sm font-bold text-[#fff1ce] backdrop-blur hover:bg-[#281a0d]"
            >
              <Package size={17} />
              <span>{content.hero.secondaryCta}</span>
            </a>
          </Reveal>

          <Reveal delay={0.24}>
            <ul className="grid gap-3 border-y border-[#d8a943]/28 py-5 text-sm font-semibold text-[#f5deb7]/82 sm:grid-cols-3">
              {content.hero.notes.map((note) => (
                <li key={note} className="flex items-center gap-2">
                  <BadgeCheck size={17} className="shrink-0 text-[#f2b53d]" />
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          </Reveal>
        </motion.div>
      </div>
    </section>
  );
}

export function V4FrustrationSection({ content }: V4SectionProps) {
  const panels = [
    {
      label: content.frustration.coldLabel,
      title: content.frustration.coldTitle,
      body: content.frustration.coldBody,
      image: v4Media.coldDinner,
      alt: content.frustration.coldAlt,
      tone: "cold",
    },
    {
      label: content.frustration.warmLabel,
      title: content.frustration.warmTitle,
      body: content.frustration.warmBody,
      image: v4Media.goldenDish,
      alt: content.frustration.warmAlt,
      tone: "warm",
    },
  ];

  return (
    <section
      id="v4-frustration-fantasy"
      className="bg-[#080706] py-16 text-[#fff8e8] md:py-24"
    >
      <div className="section-shell space-y-12">
        <Reveal className="mx-auto max-w-3xl space-y-5 text-center">
          <SectionLabel>{content.frustration.eyebrow}</SectionLabel>
          <h2 className="font-heading text-4xl font-semibold leading-tight md:text-6xl">
            {content.frustration.title}
          </h2>
          <p className="text-base leading-8 text-[#f0d7ab]/78 md:text-lg">
            {content.frustration.body}
          </p>
          <p className="mx-auto max-w-2xl font-heading text-3xl font-semibold leading-tight text-[#f2b53d]">
            {content.frustration.turn}
          </p>
        </Reveal>

        <div className="grid gap-5 lg:grid-cols-2">
          {panels.map((panel, index) => (
            <Reveal key={panel.title} delay={index * 0.1}>
              <article
                className={[
                  "relative min-h-[34rem] overflow-hidden rounded-lg border",
                  panel.tone === "cold"
                    ? "border-[#6f7784]/34 bg-[#15191d]"
                    : "border-[#d8a943]/34 bg-[#1b1007]",
                ].join(" ")}
              >
                <Image
                  src={panel.image}
                  alt={panel.alt}
                  fill
                  sizes="(max-width: 1024px) 92vw, 46vw"
                  className={[
                    "object-cover",
                    panel.tone === "cold" ? "opacity-64 grayscale-[0.2]" : "",
                  ].join(" ")}
                />
                <div
                  className={[
                    "absolute inset-0",
                    panel.tone === "cold"
                      ? "bg-[linear-gradient(180deg,rgba(9,12,15,0.16)_0%,rgba(9,12,15,0.78)_100%)]"
                      : "bg-[linear-gradient(180deg,rgba(18,9,2,0.02)_0%,rgba(18,9,2,0.78)_100%)]",
                  ].join(" ")}
                />
                <div className="absolute inset-x-0 bottom-0 z-10 space-y-3 p-6 md:p-8">
                  <p
                    className={[
                      "text-xs font-bold uppercase tracking-[0.22em]",
                      panel.tone === "cold" ? "text-[#c0cad7]" : "text-[#f2b53d]",
                    ].join(" ")}
                  >
                    {panel.label}
                  </p>
                  <h3 className="font-heading text-4xl font-semibold leading-tight">
                    {panel.title}
                  </h3>
                  <p className="max-w-xl text-sm leading-7 text-[#fff8e8]/78 md:text-base">
                    {panel.body}
                  </p>
                </div>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

export function V4ShowcaseSection({ content }: V4SectionProps) {
  return (
    <section
      id="v4-culinary-showcase"
      className="bg-[#120d08] py-16 text-[#fff8e8] md:py-24"
    >
      <div className="section-shell space-y-12">
        <Reveal className="max-w-3xl space-y-5">
          <SectionLabel>{content.showcase.eyebrow}</SectionLabel>
          <h2 className="font-heading text-4xl font-semibold leading-tight md:text-6xl">
            {content.showcase.title}
          </h2>
          <p className="text-base leading-8 text-[#f0d7ab]/78 md:text-lg">
            {content.showcase.subtitle}
          </p>
        </Reveal>

        <div className="space-y-8">
          {content.showcase.recipes.map((recipe, index) => {
            const Icon = recipeIcons[recipe.icon];
            const isReversed = index % 2 === 1;

            return (
              <Reveal key={recipe.id} delay={0.08}>
                <article
                  className={[
                    "grid overflow-hidden rounded-lg border border-[#d8a943]/28 bg-[#1c1208] shadow-[0_28px_80px_rgba(0,0,0,0.28)] lg:grid-cols-2",
                    isReversed ? "lg:[&>div:first-child]:order-2" : "",
                  ].join(" ")}
                >
                  <div className="relative min-h-[26rem] overflow-hidden">
                    <Image
                      src={recipe.image}
                      alt={recipe.imageAlt}
                      fill
                      sizes="(max-width: 1024px) 92vw, 44vw"
                      className="object-cover"
                    />
                    <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(15,9,4,0)_36%,rgba(15,9,4,0.48)_100%)]" />
                  </div>

                  <div className="flex min-h-[26rem] flex-col justify-center p-6 md:p-10">
                    <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-[#f2b53d] text-[#160d05]">
                      <Icon size={24} />
                    </div>
                    <div className="space-y-4">
                      <p className="text-xs font-bold uppercase tracking-[0.24em] text-[#f2b53d]">
                        {recipe.label}
                      </p>
                      <h3 className="font-heading text-4xl font-semibold leading-tight md:text-5xl">
                        {recipe.title}
                      </h3>
                      <p className="text-base leading-8 text-[#f0d7ab]/82">
                        {recipe.body}
                      </p>
                    </div>
                    <div className="mt-7 border-t border-[#d8a943]/22 pt-5">
                      <p className="flex items-start gap-3 text-sm font-semibold leading-7 text-[#ffe1a1]">
                        <Soup size={18} className="mt-1 shrink-0 text-[#f2b53d]" />
                        <span>{recipe.productNote}</span>
                      </p>
                    </div>
                  </div>
                </article>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export function V4SuperioritySection({ content }: V4SectionProps) {
  return (
    <section
      id="v4-superiority"
      className="bg-[#f7eddc] py-16 text-[#2a1b0d] md:py-24"
    >
      <div className="section-shell space-y-10">
        <Reveal className="mx-auto max-w-3xl space-y-4 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-[#8e6320]">
            {content.superiority.eyebrow}
          </p>
          <h2 className="font-heading text-4xl font-semibold leading-tight md:text-6xl">
            {content.superiority.title}
          </h2>
        </Reveal>

        <div className="grid gap-4 md:grid-cols-3">
          {content.superiority.items.map((item, index) => {
            const Icon = superiorityIcons[item.icon];

            return (
              <Reveal key={item.title} delay={index * 0.08}>
                <article className="h-full rounded-lg border border-[#d4b071]/50 bg-[#fffaf1] p-6 shadow-[0_20px_52px_rgba(107,72,24,0.1)]">
                  <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-[#2a1b0d] text-[#f7eddc]">
                    <Icon size={24} />
                  </div>
                  <h3 className="font-heading text-3xl font-semibold leading-tight">
                    {item.title}
                  </h3>
                  <p className="mt-4 text-sm leading-7 text-[#68513b] md:text-base">
                    {item.body}
                  </p>
                </article>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export function V4OfferSection({
  content,
  products,
  isLoading,
  onBuyNow,
}: V4OfferSectionProps) {
  const displayProducts = content.offer.items
    .map((item) => ({
      copy: item,
      product: products.find((product) => getPackKey(product) === item.packKey),
    }))
    .filter((item): item is {
      copy: (typeof content.offer.items)[number];
      product: DisplayProduct;
    } => Boolean(item.product));

  return (
    <section
      id="products"
      className="relative scroll-mt-24 bg-[#080706] py-16 text-[#fff8e8] md:py-24"
    >
      <div className="section-shell space-y-10">
        <Reveal className="mx-auto max-w-3xl space-y-5 text-center">
          <SectionLabel>{content.offer.eyebrow}</SectionLabel>
          <h2 className="font-heading text-4xl font-semibold leading-tight md:text-6xl">
            {content.offer.title}
          </h2>
          <p className="text-base leading-8 text-[#f0d7ab]/78 md:text-lg">
            {content.offer.subtitle}
          </p>
        </Reveal>

        {isLoading ? (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                key={index}
                className="min-h-[34rem] animate-pulse rounded-lg border border-[#d8a943]/20 bg-[#1c1208] p-5"
              >
                <div className="mb-5 aspect-[4/5] rounded-lg bg-[#d8a943]/12" />
                <div className="mb-3 h-5 rounded bg-[#d8a943]/12" />
                <div className="mb-6 h-10 rounded bg-[#d8a943]/12" />
                <div className="space-y-3">
                  <div className="h-4 rounded bg-[#d8a943]/12" />
                  <div className="h-4 rounded bg-[#d8a943]/12" />
                  <div className="h-4 rounded bg-[#d8a943]/12" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {displayProducts.map(({ copy, product }, index) => {
              const packKey = copy.packKey as V4PackKey;
              const isFeatured = packKey === "pack4";
              const freeShipping = Number(product.price) >= 70;

              return (
                <Reveal key={packKey} delay={index * 0.05}>
                  <article
                    className={[
                      "relative flex h-full flex-col overflow-hidden rounded-lg border bg-[#17100a] p-5 shadow-[0_26px_68px_rgba(0,0,0,0.32)]",
                      isFeatured
                        ? "border-[#f2b53d] xl:-mt-4"
                        : "border-[#d8a943]/22",
                    ].join(" ")}
                  >
                    {isFeatured ? (
                      <div className="absolute right-4 top-4 z-10 inline-flex items-center gap-2 rounded-lg bg-[#f2b53d] px-3 py-2 text-xs font-black uppercase tracking-[0.08em] text-[#140d06]">
                        <Crown size={14} />
                        <span>{content.offer.mostPopular}</span>
                      </div>
                    ) : null}

                    <div className="relative mb-5 aspect-[4/5] overflow-hidden rounded-lg border border-[#d8a943]/18 bg-[linear-gradient(180deg,#fff8e8,#f0d398)]">
                      <Image
                        src={productImagesByPack[packKey] ?? product.image}
                        alt={copy.title}
                        fill
                        sizes="(max-width: 768px) 92vw, (max-width: 1280px) 44vw, 24vw"
                        className="object-contain p-6"
                        priority={index < 2}
                      />
                    </div>

                    <div className="mb-5 space-y-3">
                      <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#f2b53d]">
                        {copy.badge}
                      </p>
                      <h3 className="font-heading text-4xl font-semibold leading-tight">
                        {copy.title}
                      </h3>
                      <p className="text-sm font-bold text-[#ffe1a1]">
                        {copy.subtitle}
                      </p>
                      <p className="text-sm leading-7 text-[#f0d7ab]/78">
                        {copy.body}
                      </p>
                      <div className="flex items-end gap-2 pt-1">
                        <span className="text-xs font-bold uppercase tracking-[0.18em] text-[#f2b53d]">
                          SGD
                        </span>
                        <span className="font-heading text-5xl font-semibold leading-none">
                          {Number(product.price).toFixed(2)}
                        </span>
                      </div>
                      {freeShipping ? (
                        <span className="inline-flex rounded-lg border border-[#f2b53d]/34 bg-[#f2b53d]/12 px-3 py-2 text-xs font-bold text-[#ffe1a1]">
                          {content.offer.freeShipping}
                        </span>
                      ) : null}
                    </div>

                    <ul className="mb-6 flex-1 space-y-3 border-t border-[#d8a943]/18 pt-5">
                      {copy.features.map((feature) => (
                        <li
                          key={feature}
                          className="flex items-start gap-3 text-sm leading-7 text-[#f0d7ab]/82"
                        >
                          <CheckCircle2
                            size={18}
                            className="mt-1 shrink-0 text-[#f2b53d]"
                          />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>

                    <button
                      id={`v4-offer-${packKey}-cta`}
                      type="button"
                      onClick={() => onBuyNow(product)}
                      className={[
                        "inline-flex min-h-13 w-full items-center justify-center gap-2 rounded-lg px-4 py-4 text-sm font-black uppercase tracking-[0.09em]",
                        isFeatured
                          ? "bg-[#f2b53d] text-[#140d06] shadow-[0_16px_34px_rgba(242,181,61,0.28)] hover:bg-[#ffd46d]"
                          : "border border-[#f2b53d]/48 bg-transparent text-[#ffe1a1] hover:bg-[#f2b53d] hover:text-[#140d06]",
                      ].join(" ")}
                    >
                      <Package size={16} />
                      <span>{content.offer.buyNow}</span>
                    </button>
                  </article>
                </Reveal>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

export function V4FinalCtaSection({ content }: V4SectionProps) {
  return (
    <section className="overflow-hidden bg-[#f7eddc] py-16 text-[#2a1b0d] md:py-24">
      <div className="section-shell grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
        <Reveal className="space-y-6">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-[#8e6320]">
            {content.finalCta.eyebrow}
          </p>
          <div className="space-y-4">
            <h2 className="font-heading text-4xl font-semibold leading-tight md:text-6xl">
              {content.finalCta.title}
            </h2>
            <p className="max-w-2xl text-base leading-8 text-[#68513b] md:text-lg">
              {content.finalCta.body}
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <a
              id="v4-final-products-cta"
              href="#products"
              className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg bg-[#2a1b0d] px-6 text-sm font-black uppercase tracking-[0.1em] text-[#fff8e8] hover:bg-[#8e6320]"
            >
              <ArrowRight size={17} />
              <span>{content.finalCta.productsCta}</span>
            </a>
            <a
              id="v4-final-whatsapp-cta"
              href={getWhatsAppHref(content.finalCta.whatsappMessage)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg border border-[#b9852e] bg-white px-6 text-sm font-bold text-[#6f4b1d] hover:bg-[#fff5e2]"
            >
              <MessageCircle size={17} />
              <span>{content.finalCta.whatsappCta}</span>
            </a>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          <div className="relative min-h-[28rem] overflow-hidden rounded-lg border border-[#d4b071]/50 bg-[#fffaf1] shadow-[0_24px_70px_rgba(107,72,24,0.14)]">
            <Image
              src={v4Media.finalTable}
              alt={content.finalCta.imageAlt}
              fill
              sizes="(max-width: 1024px) 92vw, 42vw"
              className="object-cover"
            />
            <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(42,27,13,0.08)_0%,rgba(42,27,13,0.76)_100%)]" />
          </div>
        </Reveal>
      </div>
    </section>
  );
}
