"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { Leaf, Sprout } from "lucide-react";
import V2SectionHeading from "./V2SectionHeading";
import { MotionItem, Reveal, StaggerGroup } from "./V2Motion";

export default function V2PineappleStorySection() {
  const t = useTranslations("Index.v2.pineapple");
  const points = t.raw("points") as string[];

  return (
    <section
      id="story-experience"
      className="bg-[#f8ecd5] py-16 text-[#23170d] md:py-24"
    >
      <div className="section-shell grid gap-10 lg:grid-cols-[0.94fr_1.06fr] lg:items-center">
        <Reveal
          as="figure"
          className="relative overflow-hidden rounded-lg border border-[#dcc08c] bg-[#fff7e8] shadow-[0_24px_60px_rgba(91,57,24,0.12)]"
          x={-28}
          y={18}
        >
          <div className="relative aspect-[5/4]">
            <Image
              src="/v2/aqina-v2-pineapple-farm.webp"
              alt={t("imageAlt")}
              fill
              sizes="(max-width: 1024px) 92vw, 42vw"
              className="object-cover"
            />
          </div>
          <figcaption className="border-t border-[#ead3a7] bg-white px-5 py-4 text-sm font-semibold leading-6 text-[#6f5a43]">
            {t("caption")}
          </figcaption>
        </Reveal>

        <div className="space-y-7">
          <V2SectionHeading
            eyebrow={t("eyebrow")}
            title={t("title")}
            body={t("body")}
          />

          <StaggerGroup as="ul" className="grid gap-3" staggerChildren={0.1}>
            {points.map((point, index) => (
              <MotionItem
                as="li"
                key={point}
                className="flex gap-3 rounded-lg border border-[#dcc08c] bg-white/72 px-4 py-4 text-sm leading-7 text-[#594530]"
                x={18}
                y={14}
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#f2dba8] text-[#7c531c]">
                  {index === 0 ? <Sprout size={17} /> : <Leaf size={17} />}
                </span>
                <span>{point}</span>
              </MotionItem>
            ))}
          </StaggerGroup>
        </div>
      </div>
    </section>
  );
}
