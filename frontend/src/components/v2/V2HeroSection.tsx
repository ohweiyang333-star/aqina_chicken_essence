"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import {
  ArrowRight,
  BadgeCheck,
  MessageCircle,
  ShieldCheck,
  Sparkles,
  Truck,
} from "lucide-react";

import { getWhatsAppHref } from "@/lib/site-config";
import { trackLandingFunnelEvent } from "@/lib/marketing-analytics";
import { Reveal } from "./V2Motion";

const heroImageSrc = "/v2/aqina-v2-hero-product-real.webp";

export default function V2HeroSection() {
  const t = useTranslations("Index.v2.hero");
  const badges = t.raw("badges") as string[];
  const notes = t.raw("notes") as string[];
  const trustItems = t.raw("trustItems") as string[];

  const handleProductsClick = () => {
    trackLandingFunnelEvent("hero_cta_click", {
      source: "v2_hero_products",
      destination: "products",
    });
  };

  const handleWhatsAppClick = () => {
    trackLandingFunnelEvent("whatsapp_cta_click", {
      source: "v2_hero_whatsapp",
      destination: "whatsapp",
    });
  };

  return (
    <section
      id="v2-hero"
      className="relative isolate overflow-hidden bg-[#fff7e8] pt-20 text-[#23170d] md:pt-24"
    >
      <div className="absolute inset-0 -z-20 bg-[radial-gradient(circle_at_78%_20%,rgba(233,195,113,0.32),transparent_32%),linear-gradient(180deg,#fff7e8_0%,#fffaf1_54%,#f8ecd5_100%)]" />
      <div
        className="absolute inset-0 -z-10 opacity-[0.14]"
        style={{
          backgroundImage:
            "linear-gradient(90deg, rgba(155,107,31,0.16) 1px, transparent 1px), linear-gradient(180deg, rgba(155,107,31,0.12) 1px, transparent 1px)",
          backgroundSize: "42px 42px",
        }}
      />

      <div className="section-shell relative z-10 grid gap-5 pb-8 pt-4 md:gap-7 md:pb-14 md:pt-6 lg:min-h-[calc(100svh-4rem)] lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
        <div className="flex max-w-3xl flex-col gap-4 md:gap-5">
          <Reveal
            className="hidden items-center gap-2 rounded-lg border border-[#d9b46b]/70 bg-white/78 px-4 py-2 text-xs font-bold uppercase tracking-[0.16em] text-[#8d6221] shadow-sm sm:order-1 sm:inline-flex"
            delay={0.02}
            y={12}
          >
            <Sparkles size={15} />
            <span>{t("eyebrow")}</span>
          </Reveal>

          <figure className="order-1 relative aspect-[16/7] overflow-hidden rounded-xl border border-[#d9b46b] bg-[#fffaf1] shadow-[0_16px_42px_rgba(91,57,24,0.12)] sm:hidden">
            <Image
              src={heroImageSrc}
              alt={t("imageAlt")}
              fill
              priority
              fetchPriority="high"
              sizes="92vw"
              className="object-cover object-center"
            />
          </figure>

          <Reveal className="order-2 space-y-3 sm:order-2 sm:space-y-4" delay={0.06} y={18}>
            <h1 className="max-w-[17ch] font-heading text-[2.1rem] font-semibold leading-[1.04] text-[#20150c] sm:max-w-[18ch] sm:text-[3.15rem] md:text-[4rem]">
              {t("title")}
            </h1>
            <p className="max-w-2xl text-sm leading-7 text-[#5e4934] sm:text-base md:text-lg md:leading-8">
              {t("subtitle")}
            </p>
          </Reveal>

          <Reveal
            className="order-4 grid grid-cols-2 gap-2.5 sm:order-3 sm:grid-cols-2 sm:gap-3"
            delay={0.1}
            y={14}
          >
            <p className="hidden min-h-10 items-center justify-center gap-2 rounded-lg border border-[#d9b46b]/65 bg-[#fffaf1]/82 px-4 text-xs font-bold uppercase tracking-[0.12em] text-[#7a5220] sm:col-span-2 sm:flex">
              <span>{t("priceLine")}</span>
              <span className="text-[#c99a4c]">/</span>
              <span>{notes[0]}</span>
            </p>
            <a
              id="v2-hero-products-cta"
              href="#products"
              onClick={handleProductsClick}
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[#1b130c] px-3 text-xs font-bold text-[#fff7e8] shadow-[0_16px_32px_rgba(52,32,13,0.2)] transition hover:-translate-y-0.5 hover:bg-[#8d6221] hover:shadow-[0_20px_38px_rgba(52,32,13,0.24)] sm:px-6 sm:text-sm"
            >
              <span>{t("primaryCta")}</span>
              <ArrowRight size={17} />
            </a>
            <a
              id="v2-hero-whatsapp-cta"
              href={getWhatsAppHref(t("whatsappMessage"))}
              target="_blank"
              rel="noopener noreferrer"
              onClick={handleWhatsAppClick}
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-[#c99a4c] bg-white/82 px-3 text-xs font-bold text-[#5b3918] transition hover:-translate-y-0.5 hover:border-[#8d6221] hover:bg-white hover:shadow-[0_16px_30px_rgba(91,57,24,0.12)] sm:px-6 sm:text-sm"
            >
              <MessageCircle size={17} />
              <span>{t("whatsappCta")}</span>
            </a>
          </Reveal>

          <Reveal
            as="ul"
            className="order-5 grid max-w-2xl gap-2 sm:order-5 sm:grid-cols-3"
            delay={0.14}
            y={16}
          >
            {trustItems.map((item, index) => {
              const Icon = index === 2 ? Truck : index === 1 ? ShieldCheck : BadgeCheck;

              return (
                <li
                  key={item}
                  className="flex min-h-11 items-center gap-2 rounded-lg border border-[#e0bd76] bg-white/76 px-3 py-2 text-xs font-bold leading-5 text-[#4d351f] shadow-sm sm:min-h-12 sm:text-sm"
                >
                  <Icon size={17} className="shrink-0 text-[#9b6b1f]" />
                  <span>{item}</span>
                </li>
              );
            })}
          </Reveal>

          <Reveal
            className="order-3 grid max-w-2xl grid-cols-[0.82fr_1.18fr] gap-3 rounded-lg border border-[#d9b46b]/65 bg-[#fffaf1]/82 p-3 text-sm text-[#594530] sm:order-4 sm:grid-cols-[0.9fr_1.1fr] sm:p-4"
            delay={0.18}
            y={16}
          >
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#9b6b1f]">
                {t("priceLabel")}
              </p>
              <p className="mt-1 font-heading text-[1.45rem] font-semibold leading-tight text-[#20150c] sm:text-3xl">
                {t("priceLine")}
              </p>
            </div>
            <div className="space-y-1.5 border-l border-[#d9b46b]/55 pl-3 sm:space-y-2 sm:pl-4">
              {notes.map((note) => (
                <p key={note} className="flex items-center gap-2 text-xs font-semibold leading-5 sm:text-sm sm:leading-6">
                  <BadgeCheck size={15} className="shrink-0 text-[#9b6b1f]" />
                  <span>{note}</span>
                </p>
              ))}
            </div>
          </Reveal>
        </div>

        <div className="relative mx-auto hidden w-full max-w-[38rem] sm:block">
          <div className="absolute -left-4 top-8 z-10 rounded-lg border border-[#d9b46b] bg-white/88 px-4 py-3 text-sm font-bold text-[#5b3918] shadow-[0_18px_42px_rgba(91,57,24,0.14)] backdrop-blur">
            {badges[0]}
          </div>
          <div className="absolute -right-2 bottom-8 z-10 rounded-lg border border-[#d9b46b] bg-[#1b130c]/92 px-4 py-3 text-sm font-bold text-[#fff7e8] shadow-[0_18px_42px_rgba(91,57,24,0.18)] backdrop-blur">
            {badges[1]}
          </div>
          <figure className="relative aspect-[4/3] overflow-hidden rounded-2xl border border-[#d9b46b] bg-[linear-gradient(135deg,#fffaf1,#efd394)] shadow-[0_26px_80px_rgba(91,57,24,0.18)]">
            <Image
              src={heroImageSrc}
              alt={t("imageAlt")}
              fill
              priority
              fetchPriority="high"
              sizes="(max-width: 1024px) 92vw, 48vw"
              className="object-cover object-center"
            />
          </figure>
        </div>
      </div>
    </section>
  );
}
