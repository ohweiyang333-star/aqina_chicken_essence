"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { Droplets, Flame, PackageCheck, Soup } from "lucide-react";
import V2SectionHeading from "./V2SectionHeading";
import { MotionItem, Reveal, StaggerGroup } from "./V2Motion";

interface CraftStep {
  title: string;
  body: string;
}

const icons = [Soup, Flame, Droplets, PackageCheck] as const;

export default function V2CraftLightnessSection() {
  const t = useTranslations("Index.v2.craft");
  const steps = t.raw("steps") as CraftStep[];

  return (
    <section id="v2-craft-lightness" className="bg-[#fffaf1] py-16 md:py-24">
      <div className="section-shell space-y-10">
        <div className="grid gap-8 lg:grid-cols-[1fr_0.82fr] lg:items-end">
          <V2SectionHeading
            eyebrow={t("eyebrow")}
            title={t("title")}
            body={t("body")}
          />
          <Reveal
            as="p"
            className="rounded-lg border border-[#ead3a7] bg-[#fff7e8] px-5 py-4 text-sm leading-7 text-[#6f5a43]"
            delay={0.08}
            x={20}
          >
            {t("note")}
          </Reveal>
        </div>

        <StaggerGroup
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
          staggerChildren={0.09}
        >
          {steps.map((step, index) => {
            const Icon = icons[index % icons.length];

            return (
              <MotionItem
                as="article"
                key={step.title}
                className="rounded-lg border border-[#ead3a7] bg-white px-5 py-6 shadow-[0_12px_34px_rgba(91,57,24,0.06)] hover:-translate-y-1 hover:shadow-[0_18px_42px_rgba(91,57,24,0.1)]"
                y={24}
              >
                <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-lg bg-[#f2dba8] text-[#7c531c]">
                  <Icon size={20} />
                </div>
                <h3 className="text-lg font-bold text-[#23170d]">
                  {step.title}
                </h3>
                <p className="mt-3 text-sm leading-7 text-[#6f5a43]">
                  {step.body}
                </p>
              </MotionItem>
            );
          })}
        </StaggerGroup>

        <Reveal
          as="figure"
          className="grid overflow-hidden rounded-lg border border-[#e2c894] bg-[#1b130c] text-[#fff7e8] md:grid-cols-[0.95fr_1.05fr]"
          scale={0.96}
          y={32}
        >
          <div className="relative min-h-72">
            <Image
              src="/v2/aqina-v2-golden-essence.webp"
              alt={t("ritualImageAlt")}
              fill
              sizes="(max-width: 768px) 92vw, 44vw"
              className="object-cover"
            />
          </div>
          <figcaption className="flex flex-col justify-center gap-4 p-6 md:p-8">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#e9c371]">
              {t("ritualEyebrow")}
            </p>
            <h3 className="font-heading text-3xl font-semibold leading-tight md:text-4xl">
              {t("ritualTitle")}
            </h3>
            <p className="text-sm leading-7 text-[#f5dfb7]/82 md:text-base">
              {t("ritualBody")}
            </p>
          </figcaption>
        </Reveal>
      </div>
    </section>
  );
}
