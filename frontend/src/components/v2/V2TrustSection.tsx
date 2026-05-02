"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { BadgeCheck, ShieldCheck, Store } from "lucide-react";
import { IMAGES } from "@/lib/image-utils";
import V2SectionHeading from "./V2SectionHeading";
import { MotionItem, StaggerGroup } from "./V2Motion";

const certifications = [
  {
    id: "haccp-gmp-iso",
    src: IMAGES.trust.complianceBadge,
    altKey: "certifications.haccp.alt",
    labelKey: "certifications.haccp.label",
  },
  {
    id: "jakim-halal",
    src: IMAGES.trust.halalBadge,
    altKey: "certifications.halal.alt",
    labelKey: "certifications.halal.label",
  },
  {
    id: "jph-veterinary",
    src: IMAGES.trust.veterinaryBadge,
    altKey: "certifications.veterinary.alt",
    labelKey: "certifications.veterinary.label",
  },
] as const;

const retailers = [
  { id: "jaya-grocer", name: "Jaya Grocer", src: "/brands/jaya-grocer.png" },
  { id: "aeon", name: "AEON", src: "/brands/aeon.svg" },
  { id: "lotuss", name: "Lotus's", src: "/brands/lotuss.svg" },
  {
    id: "village-grocer",
    name: "Village Grocer",
    src: "/brands/village-grocer.jpg",
  },
] as const;

export default function V2TrustSection() {
  const t = useTranslations("Index.v2.trust");
  const bullets = t.raw("bullets") as string[];

  return (
    <section id="v2-trust" className="bg-[#fffaf1] py-16 md:py-24">
      <div className="section-shell space-y-10">
        <V2SectionHeading
          eyebrow={t("eyebrow")}
          title={t("title")}
          body={t("body")}
          align="center"
        />

        <StaggerGroup
          className="grid gap-4 md:grid-cols-3"
          staggerChildren={0.1}
        >
          {certifications.map((certification) => (
            <MotionItem
              as="article"
              key={certification.id}
              className="rounded-lg border border-[#dcc08c] bg-white px-5 py-5 text-center shadow-[0_14px_34px_rgba(91,57,24,0.07)] hover:-translate-y-1 hover:shadow-[0_18px_42px_rgba(91,57,24,0.1)]"
              y={22}
            >
              <div className="relative mx-auto h-20 w-full">
                <Image
                  src={certification.src}
                  alt={t(certification.altKey)}
                  fill
                  sizes="(max-width: 768px) 60vw, 260px"
                  className="object-contain"
                />
              </div>
              <p className="mt-4 text-xs font-bold uppercase tracking-[0.14em] text-[#6d451d]">
                {t(certification.labelKey)}
              </p>
            </MotionItem>
          ))}
        </StaggerGroup>

        <StaggerGroup
          className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]"
          staggerChildren={0.12}
        >
          <MotionItem
            as="article"
            className="rounded-lg border border-[#e2c894] bg-[#1b130c] p-6 text-[#fff7e8] md:p-7"
            x={-18}
          >
            <div className="inline-flex items-center gap-2 rounded-lg border border-[#e9c371]/35 px-3 py-2 text-xs font-bold uppercase tracking-[0.14em] text-[#e9c371]">
              <ShieldCheck size={15} />
              <span>{t("assuranceEyebrow")}</span>
            </div>
            <ul className="mt-5 space-y-4">
              {bullets.map((bullet) => (
                <li key={bullet} className="flex gap-3 text-sm leading-7">
                  <BadgeCheck
                    size={18}
                    className="mt-1 shrink-0 text-[#e9c371]"
                  />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </MotionItem>

          <MotionItem
            as="article"
            className="rounded-lg border border-[#dcc08c] bg-white p-6 md:p-7"
            x={18}
          >
            <div className="mb-5 flex items-center gap-2 text-sm font-bold uppercase tracking-[0.14em] text-[#6d451d]">
              <Store size={17} />
              <span>{t("retailTitle")}</span>
            </div>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {retailers.map((retailer) => (
                <div
                  key={retailer.id}
                  className="rounded-lg border border-[#ead3a7] bg-[#fffaf1] px-3 py-4"
                >
                  <div className="relative h-12">
                    <Image
                      src={retailer.src}
                      alt={retailer.name}
                      fill
                      sizes="(max-width: 768px) 42vw, 160px"
                      className="object-contain"
                    />
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-5 text-sm leading-7 text-[#6f5a43]">
              {t("retailNote")}
            </p>
          </MotionItem>
        </StaggerGroup>
      </div>
    </section>
  );
}
