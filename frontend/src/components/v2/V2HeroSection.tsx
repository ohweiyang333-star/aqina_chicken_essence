"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { ArrowRight, CheckCircle2, ShieldCheck, Sparkles } from "lucide-react";

export default function V2HeroSection() {
  const t = useTranslations("Index.v2.hero");
  const badges = t.raw("badges") as string[];
  const notes = t.raw("notes") as string[];

  return (
    <section
      id="v2-hero"
      className="relative isolate overflow-hidden bg-[#fff7e8] pt-24 text-[#23170d] md:pt-28"
    >
      <Image
        src="/v2/aqina-v2-hero.webp"
        alt={t("imageAlt")}
        fill
        priority
        sizes="100vw"
        className="absolute inset-0 -z-20 object-cover object-[68%_center]"
      />
      <div className="absolute inset-0 -z-10 bg-[linear-gradient(90deg,#fff7e8_0%,rgba(255,247,232,0.95)_32%,rgba(255,247,232,0.48)_62%,rgba(255,247,232,0.08)_100%)]" />
      <div className="absolute inset-0 -z-10 bg-[linear-gradient(180deg,rgba(255,247,232,0.15)_0%,rgba(255,247,232,0.08)_62%,#fff7e8_100%)]" />
      <div
        className="absolute inset-0 -z-10 opacity-[0.18]"
        style={{
          backgroundImage:
            "linear-gradient(90deg, rgba(155,107,31,0.16) 1px, transparent 1px), linear-gradient(180deg, rgba(155,107,31,0.12) 1px, transparent 1px)",
          backgroundSize: "42px 42px",
        }}
      />
      <div className="section-shell grid min-h-[calc(100vh-4rem)] gap-10 pb-14 pt-10 md:pb-20 lg:grid-cols-[1.02fr_0.98fr] lg:items-center">
        <div className="max-w-3xl space-y-7">
          <div className="inline-flex items-center gap-2 rounded-lg border border-[#d9b46b]/60 bg-white/72 px-4 py-2 text-xs font-bold uppercase tracking-[0.16em] text-[#8d6221] shadow-sm">
            <Sparkles size={15} />
            <span>{t("eyebrow")}</span>
          </div>

          <div className="space-y-5">
            <h1 className="font-heading text-5xl font-semibold leading-[0.98] text-[#20150c] md:text-7xl">
              {t("title")}
            </h1>
            <p className="max-w-2xl text-base leading-8 text-[#6f5a43] md:text-xl">
              {t("subtitle")}
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <a
              id="v2-hero-products-cta"
              href="#products"
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[#1b130c] px-6 text-sm font-bold text-[#fff7e8] shadow-[0_16px_32px_rgba(52,32,13,0.2)] hover:bg-[#8d6221]"
            >
              <span>{t("primaryCta")}</span>
              <ArrowRight size={17} />
            </a>
            <a
              id="v2-hero-ugc-cta"
              href="#ugc-reviews"
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-[#c99a4c] bg-white/72 px-6 text-sm font-bold text-[#5b3918] hover:border-[#8d6221] hover:bg-white"
            >
              <ShieldCheck size={17} />
              <span>{t("secondaryCta")}</span>
            </a>
          </div>

          <ul className="grid gap-3 text-sm text-[#594530] sm:grid-cols-3">
            {badges.map((badge) => (
              <li
                key={badge}
                className="flex items-start gap-2 rounded-lg border border-[#ead3a7] bg-white/58 px-3 py-3"
              >
                <CheckCircle2
                  size={17}
                  className="mt-0.5 shrink-0 text-[#9b6b1f]"
                />
                <span>{badge}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="relative flex min-h-[28rem] items-end lg:min-h-[34rem]">
          <div className="grid w-full gap-3 sm:grid-cols-3 lg:absolute lg:bottom-0 lg:right-0 lg:max-w-xl">
            {notes.map((note) => (
              <div
                key={note}
                className="rounded-lg border border-[#ead3a7] bg-white/82 px-4 py-3 text-sm font-semibold leading-6 text-[#4d3826] shadow-sm backdrop-blur"
              >
                {note}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
