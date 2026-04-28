"use client";

import Image from "next/image";
import {
  ArrowRight,
  BadgeCheck,
  Droplets,
  HeartHandshake,
  Leaf,
  MessageCircle,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { getWhatsAppHref } from "@/lib/site-config";
import { IMAGES } from "@/lib/image-utils";

interface PainItem {
  title: string;
  body: string;
  image: string;
  alt: string;
}

interface SolutionItem {
  title: string;
  body: string;
  icon: "pineapple" | "droplet" | "shield";
}

interface CertificationItem {
  id: "haccp" | "halal" | "veterinary";
  alt: string;
  label: string;
}

interface StoryItem {
  name: string;
  role: string;
  quote: string;
  image: string;
  alt: string;
}

const solutionIcons = {
  pineapple: Leaf,
  droplet: Droplets,
  shield: ShieldCheck,
} as const;

const certificationSources = {
  haccp: IMAGES.trust.complianceBadge,
  halal: IMAGES.trust.halalBadge,
  veterinary: IMAGES.trust.veterinaryBadge,
} as const;

export function V3HeroSection() {
  const t = useTranslations("Index.v3.hero");
  const notes = t.raw("notes") as string[];

  return (
    <section
      id="v3-hero"
      className="relative isolate min-h-[calc(100vh-4rem)] overflow-hidden bg-[#f7eddc] text-[#2f2418]"
    >
      <Image
        src="/v3/maternity-hero.jpg"
        alt={t("imageAlt")}
        fill
        priority
        sizes="100vw"
        className="absolute inset-0 -z-30 object-cover object-[64%_center]"
      />
      <div className="absolute inset-0 -z-20 bg-[linear-gradient(90deg,#f7eddc_0%,rgba(247,237,220,0.96)_34%,rgba(247,237,220,0.58)_64%,rgba(247,237,220,0.12)_100%)]" />
      <div className="absolute inset-0 -z-10 bg-[linear-gradient(180deg,rgba(247,237,220,0.15)_0%,rgba(247,237,220,0.02)_62%,#f7eddc_100%)]" />

      <div className="section-shell grid min-h-[calc(100vh-4rem)] items-center gap-8 pb-16 pt-28 lg:grid-cols-[0.98fr_1.02fr]">
        <div className="max-w-3xl space-y-7">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#d5b36b]/70 bg-white/72 px-4 py-2 text-xs font-bold text-[#8b6122] shadow-sm backdrop-blur">
            <Sparkles size={15} />
            <span>{t("eyebrow")}</span>
          </div>

          <div className="space-y-5">
            <p className="font-heading text-2xl font-semibold leading-tight text-[#8b6122]">
              {t("kicker")}
            </p>
            <h1 className="font-heading text-5xl font-semibold leading-[1.02] text-[#2f2418] md:text-7xl">
              {t("title")}
            </h1>
            <p className="max-w-2xl text-base leading-8 text-[#6c5848] md:text-xl">
              {t("subtitle")}
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <a
              id="v3-hero-products-cta"
              href="#products"
              className="v3-breathing-cta inline-flex min-h-14 items-center justify-center gap-2 rounded-lg bg-[#2f2418] px-6 text-sm font-bold text-[#fffaf1] shadow-[0_18px_38px_rgba(47,36,24,0.24)] hover:bg-[#8b6122]"
            >
              <span>{t("primaryCta")}</span>
              <ArrowRight size={17} />
            </a>
            <a
              id="v3-hero-stories-cta"
              href="#v3-stories"
              className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg border border-[#b9852e] bg-white/70 px-6 text-sm font-bold text-[#6f4b1d] backdrop-blur hover:bg-white"
            >
              <HeartHandshake size={17} />
              <span>{t("secondaryCta")}</span>
            </a>
          </div>

          <ul className="grid gap-3 border-y border-[#c99744]/40 py-5 text-sm font-semibold text-[#5f4d3e] sm:grid-cols-3">
            {notes.map((note) => (
              <li key={note} className="flex items-center gap-2">
                <BadgeCheck size={17} className="shrink-0 text-[#79946c]" />
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="hidden lg:block" />
      </div>
    </section>
  );
}

export function V3EmpathySection() {
  const t = useTranslations("Index.v3.empathy");
  const items = t.raw("items") as PainItem[];

  return (
    <section className="bg-[#2f2418] py-16 text-[#fffaf1] md:py-24">
      <div className="section-shell space-y-10">
        <div className="mx-auto max-w-3xl space-y-4 text-center">
          <p className="text-xs font-bold uppercase text-[#e5c77b]">
            {t("eyebrow")}
          </p>
          <h2 className="font-heading text-4xl font-semibold leading-tight md:text-5xl">
            {t("title")}
          </h2>
          <p className="text-base leading-8 text-[#ead8bd]/82 md:text-lg">
            {t("body")}
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          {items.map((item, index) => (
            <article
              key={item.title}
              className="v3-soft-reveal overflow-hidden rounded-lg border border-[#d7b56c]/24 bg-[#3a2c1d]"
              style={{ animationDelay: `${index * 90}ms` }}
            >
              <div className="relative aspect-[4/5]">
                <Image
                  src={item.image}
                  alt={item.alt}
                  fill
                  sizes="(max-width: 1024px) 92vw, 30vw"
                  className="object-cover"
                />
                <div className="absolute inset-0 bg-[linear-gradient(180deg,transparent_42%,rgba(47,36,24,0.72)_100%)]" />
              </div>
              <div className="space-y-3 p-5">
                <p className="font-heading text-2xl font-semibold text-[#f7e2aa]">
                  {item.title}
                </p>
                <p className="text-sm leading-7 text-[#fffaf1]/78">
                  {item.body}
                </p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function V3SolutionSection() {
  const t = useTranslations("Index.v3.solution");
  const items = t.raw("items") as SolutionItem[];

  return (
    <section className="bg-[#fffaf1] py-16 text-[#2f2418] md:py-24">
      <div className="section-shell grid gap-10 lg:grid-cols-[0.86fr_1.14fr] lg:items-center">
        <div className="space-y-6">
          <div className="space-y-4">
            <p className="text-xs font-bold uppercase text-[#8b6f38]">
              {t("eyebrow")}
            </p>
            <h2 className="font-heading text-4xl font-semibold leading-tight md:text-5xl">
              {t("title")}
            </h2>
            <p className="text-base leading-8 text-[#725f4d] md:text-lg">
              {t("body")}
            </p>
          </div>

          <div className="relative aspect-[4/5] overflow-hidden rounded-lg border border-[#d9c6a9]">
            <Image
              src="/v3/light-ritual.jpg"
              alt={t("imageAlt")}
              fill
              sizes="(max-width: 1024px) 92vw, 38vw"
              className="object-cover"
            />
          </div>
        </div>

        <div className="grid gap-4">
          {items.map((item) => {
            const Icon = solutionIcons[item.icon];

            return (
              <article
                key={item.title}
                className="rounded-lg border border-[#d9c6a9] bg-[#f7eddc] p-6 shadow-[0_18px_50px_rgba(103,70,28,0.08)]"
              >
                <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-[#2f5c46] text-[#fffaf1]">
                  <Icon size={24} />
                </div>
                <h3 className="font-heading text-3xl font-semibold leading-tight">
                  {item.title}
                </h3>
                <p className="mt-3 text-sm leading-7 text-[#725f4d] md:text-base">
                  {item.body}
                </p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export function V3CertificationsSection() {
  const t = useTranslations("Index.v3.certifications");
  const certifications = t.raw("items") as CertificationItem[];

  return (
    <section
      id="v3-certifications"
      className="bg-[#08291e] py-14 text-[#f9f4e8] md:py-20"
    >
      <div className="section-shell space-y-7">
        <div className="max-w-3xl space-y-3">
          <p className="text-xs font-bold uppercase tracking-[0.28em] text-[#b8d7c5]">
            {t("eyebrow")}
          </p>
          <h2 className="font-heading text-4xl font-semibold leading-tight md:text-5xl">
            {t("title")}
          </h2>
          <p className="text-base leading-8 text-[#d6e6dc]/82 md:text-lg">
            {t("body")}
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {certifications.map((certification) => (
            <article
              key={certification.id}
              className="rounded-lg border border-[#8eb99f]/40 bg-white px-5 py-6 text-center text-[#123225] shadow-[0_22px_60px_rgba(0,0,0,0.18)]"
            >
              <div className="relative mx-auto h-24 w-full">
                <Image
                  src={certificationSources[certification.id]}
                  alt={certification.alt}
                  fill
                  sizes="(max-width: 768px) 70vw, 280px"
                  className="object-contain"
                />
              </div>
              <p className="mt-5 text-xs font-bold uppercase tracking-[0.2em] text-[#2f7a58]">
                {certification.label}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function V3StoriesSection() {
  const t = useTranslations("Index.v3.stories");
  const stories = t.raw("items") as StoryItem[];

  return (
    <section id="v3-stories" className="bg-[#eef2e8] py-16 text-[#263626] md:py-24">
      <div className="section-shell space-y-10">
        <div className="mx-auto max-w-3xl space-y-4 text-center">
          <p className="text-xs font-bold uppercase text-[#6f8a63]">
            {t("eyebrow")}
          </p>
          <h2 className="font-heading text-4xl font-semibold leading-tight md:text-5xl">
            {t("title")}
          </h2>
          <p className="text-base leading-8 text-[#5d6c58] md:text-lg">
            {t("body")}
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stories.map((story, index) => (
            <article
              key={`${story.name}-${story.role}`}
              className="overflow-hidden rounded-lg border border-[#cbd8c3] bg-white shadow-[0_18px_44px_rgba(64,83,55,0.08)]"
            >
              <div className="relative aspect-[4/5]">
                <Image
                  src={story.image}
                  alt={story.alt}
                  fill
                  priority={index < 2}
                  sizes="(max-width: 768px) 92vw, (max-width: 1024px) 44vw, 23vw"
                  className="object-cover"
                />
              </div>
              <div className="space-y-4 p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-[#263626]">{story.name}</h3>
                    <p className="text-xs font-bold uppercase text-[#6f8a63]">
                      {story.role}
                    </p>
                  </div>
                  <MessageCircle size={18} className="shrink-0 text-[#6f8a63]" />
                </div>
                <p className="text-sm leading-7 text-[#53604f]">
                  &ldquo;{story.quote}&rdquo;
                </p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function V3FinalCtaSection() {
  const t = useTranslations("Index.v3.finalCta");

  return (
    <section className="relative overflow-hidden bg-[#fffaf1] py-16 text-[#2f2418] md:py-24">
      <div className="section-shell grid gap-8 lg:grid-cols-[1.08fr_0.92fr] lg:items-center">
        <div className="space-y-6">
          <p className="text-xs font-bold uppercase text-[#8b6f38]">
            {t("eyebrow")}
          </p>
          <div className="space-y-4">
            <h2 className="font-heading text-4xl font-semibold leading-tight md:text-6xl">
              {t("title")}
            </h2>
            <p className="max-w-2xl text-base leading-8 text-[#725f4d] md:text-lg">
              {t("body")}
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <a
              id="v3-final-products-cta"
              href="#products"
              className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg bg-[#2f2418] px-6 text-sm font-bold text-[#fffaf1] hover:bg-[#8b6122]"
            >
              <span>{t("productsCta")}</span>
              <ArrowRight size={17} />
            </a>
            <a
              id="v3-final-whatsapp-cta"
              href={getWhatsAppHref(t("whatsappMessage"))}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg border border-[#b9852e] bg-white px-6 text-sm font-bold text-[#6f4b1d] hover:bg-[#fff5e2]"
            >
              <MessageCircle size={17} />
              <span>{t("whatsappCta")}</span>
            </a>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="relative aspect-[4/5] overflow-hidden rounded-lg border border-[#d9c6a9]">
            <Image
              src="/v3/ugc-partner-care.jpg"
              alt={t("imageAlt")}
              fill
              sizes="(max-width: 1024px) 44vw, 22vw"
              className="object-cover"
            />
          </div>
          <div className="rounded-lg border border-[#d9c6a9] bg-[#f7eddc] p-5">
            <div className="relative mx-auto mb-4 aspect-[4/5] max-w-[12rem]">
              <Image
                src={IMAGES.products.box4}
                alt={t("productAlt")}
                fill
                sizes="12rem"
                className="object-contain"
              />
            </div>
            <p className="text-sm font-bold leading-7 text-[#5d4b3c]">
              {t("productNote")}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
