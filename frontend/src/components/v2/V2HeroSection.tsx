"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { ArrowRight, ShieldCheck, Sparkles } from "lucide-react";
import {
  motion,
  useScroll,
  useTransform,
} from "framer-motion";

import {
  MotionItem,
  Reveal,
  StaggerGroup,
  useV2ReducedMotion,
} from "./V2Motion";

export default function V2HeroSection() {
  const t = useTranslations("Index.v2.hero");
  const badges = t.raw("badges") as string[];
  const notes = t.raw("notes") as string[];
  const heroImageSrc = "/v2/aqina-v2-hero-product-real.webp";
  const shouldReduceMotion = useV2ReducedMotion();
  const { scrollY } = useScroll();
  const imageY = useTransform(scrollY, [0, 800], [0, 72]);
  const copyY = useTransform(scrollY, [0, 800], [0, -34]);

  return (
    <section
      id="v2-hero"
      className="relative isolate overflow-hidden bg-[#fff7e8] pt-24 text-[#23170d] md:pt-28"
    >
      <motion.div
        className="absolute -inset-y-16 inset-x-0 -z-20 lg:hidden"
        style={shouldReduceMotion ? undefined : { y: imageY }}
      >
        <Image
          src={heroImageSrc}
          alt={t("imageAlt")}
          fill
          sizes="100vw"
          className="object-cover object-[58%_center]"
        />
      </motion.div>
      <motion.div
        className="absolute -inset-y-16 right-0 -z-20 hidden w-[52%] lg:block"
        style={shouldReduceMotion ? undefined : { y: imageY }}
      >
        <Image
          src={heroImageSrc}
          alt={t("imageAlt")}
          fill
          priority
          sizes="52vw"
          className="object-cover object-center"
        />
      </motion.div>
      <div className="absolute inset-0 -z-10 bg-[linear-gradient(90deg,#fff7e8_0%,rgba(255,247,232,0.96)_38%,rgba(255,247,232,0.52)_68%,rgba(255,247,232,0.08)_100%)] lg:bg-[linear-gradient(90deg,#fff7e8_0%,#fff7e8_46%,rgba(255,247,232,0.76)_53%,rgba(255,247,232,0.18)_70%,rgba(255,247,232,0.02)_100%)]" />
      <div className="absolute inset-0 -z-10 bg-[linear-gradient(180deg,rgba(255,247,232,0.1)_0%,rgba(255,247,232,0.05)_62%,#fff7e8_100%)]" />
      <div
        className="absolute inset-0 -z-10 opacity-[0.18]"
        style={{
          backgroundImage:
            "linear-gradient(90deg, rgba(155,107,31,0.16) 1px, transparent 1px), linear-gradient(180deg, rgba(155,107,31,0.12) 1px, transparent 1px)",
          backgroundSize: "42px 42px",
        }}
      />
      <div className="section-shell grid min-h-[calc(100vh-4rem)] gap-10 pb-14 pt-10 md:pb-20 lg:grid-cols-[1.02fr_0.98fr] lg:items-center">
        <motion.div
          className="max-w-3xl space-y-7"
          style={shouldReduceMotion ? undefined : { y: copyY }}
        >
          <Reveal
            className="inline-flex items-center gap-2 rounded-lg border border-[#d9b46b]/60 bg-white/72 px-4 py-2 text-xs font-bold uppercase tracking-[0.16em] text-[#8d6221] shadow-sm"
            delay={0.02}
            y={18}
          >
            <Sparkles size={15} />
            <span>{t("eyebrow")}</span>
          </Reveal>

          <Reveal className="space-y-5" delay={0.1} y={28}>
            <h1 className="font-heading text-5xl font-semibold leading-[0.98] text-[#20150c] md:text-7xl">
              {t("title")}
            </h1>
            <p className="max-w-2xl text-base leading-8 text-[#6f5a43] md:text-xl">
              {t("subtitle")}
            </p>
          </Reveal>

          <Reveal className="flex flex-col gap-3 sm:flex-row" delay={0.18}>
            <a
              id="v2-hero-products-cta"
              href="#products"
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[#1b130c] px-6 text-sm font-bold text-[#fff7e8] shadow-[0_16px_32px_rgba(52,32,13,0.2)] hover:-translate-y-0.5 hover:bg-[#8d6221] hover:shadow-[0_20px_38px_rgba(52,32,13,0.24)]"
            >
              <span>{t("primaryCta")}</span>
              <ArrowRight size={17} />
            </a>
            <a
              id="v2-hero-ugc-cta"
              href="#ugc-reviews"
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-[#c99a4c] bg-white/72 px-6 text-sm font-bold text-[#5b3918] hover:-translate-y-0.5 hover:border-[#8d6221] hover:bg-white hover:shadow-[0_16px_30px_rgba(91,57,24,0.12)]"
            >
              <ShieldCheck size={17} />
              <span>{t("secondaryCta")}</span>
            </a>
          </Reveal>

          <StaggerGroup
            as="ul"
            className="grid max-w-2xl gap-4 border-y border-[#d9b46b]/45 py-5 text-sm text-[#594530] sm:grid-cols-3"
            delayChildren={0.26}
          >
            {badges.map((badge, index) => (
              <MotionItem
                as="li"
                key={badge}
                className="relative flex items-center gap-3 sm:pr-5"
                y={18}
              >
                <span className="font-heading text-xl leading-none text-[#b98220]">
                  0{index + 1}
                </span>
                <span className="h-7 w-px bg-[#d9b46b]/55" />
                <span className="font-semibold leading-6">{badge}</span>
              </MotionItem>
            ))}
          </StaggerGroup>
        </motion.div>

        <div className="relative flex min-h-[28rem] items-end lg:min-h-[34rem]">
          <Reveal
            className="w-full border-t border-[#d9b46b]/65 pt-4 lg:absolute lg:bottom-0 lg:right-0 lg:max-w-xl"
            delay={0.34}
            x={24}
          >
            <p className="text-[0.72rem] font-bold tracking-[0.22em] text-[#8d6221]">
              {t("proofLabel")}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm font-semibold leading-6 text-[#4d3826]">
              {notes.map((note, index) => (
                <span key={note} className="inline-flex items-center gap-3">
                  <span>{note}</span>
                  {index < notes.length - 1 ? (
                    <span className="h-1.5 w-1.5 rounded-full bg-[#b98220]/75" />
                  ) : null}
                </span>
              ))}
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
