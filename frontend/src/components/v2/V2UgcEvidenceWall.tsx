"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { MessageCircle } from "lucide-react";
import V2SectionHeading from "./V2SectionHeading";
import { MotionItem, Reveal, StaggerGroup } from "./V2Motion";

interface UGCItem {
  name: string;
  context: string;
  quote: string;
  image: string;
  alt: string;
}

export default function V2UgcEvidenceWall() {
  const t = useTranslations("Index.v2.ugc");
  const items = t.raw("items") as UGCItem[];

  return (
    <section id="ugc-reviews" className="bg-[#f8ecd5] py-16 md:py-24">
      <div className="section-shell space-y-10">
        <V2SectionHeading
          eyebrow={t("eyebrow")}
          title={t("title")}
          body={t("body")}
          align="center"
        />

        <StaggerGroup
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
          staggerChildren={0.1}
        >
          {items.map((item, index) => (
            <MotionItem
              as="article"
              key={`${item.name}-${item.context}`}
              className="overflow-hidden rounded-lg border border-[#dcc08c] bg-white shadow-[0_14px_34px_rgba(91,57,24,0.07)] hover:-translate-y-1 hover:shadow-[0_20px_44px_rgba(91,57,24,0.11)]"
              y={24}
            >
              <div className="relative aspect-[4/3]">
                <Image
                  src={item.image}
                  alt={item.alt}
                  fill
                  priority={index < 2}
                  sizes="(max-width: 768px) 92vw, (max-width: 1024px) 44vw, 30vw"
                  className="object-cover"
                />
              </div>
              <div className="space-y-4 p-5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-[#23170d]">{item.name}</h3>
                    <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#9b6b1f]">
                      {item.context}
                    </p>
                  </div>
                  <MessageCircle
                    size={18}
                    className="shrink-0 text-[#9b6b1f]"
                  />
                </div>
                <p className="text-sm leading-7 text-[#6f5a43]">
                  &ldquo;{item.quote}&rdquo;
                </p>
              </div>
            </MotionItem>
          ))}
        </StaggerGroup>

        <Reveal
          as="p"
          className="mx-auto max-w-3xl text-center text-xs leading-6 text-[#7b6958]"
          y={16}
        >
          {t("disclaimer")}
        </Reveal>
      </div>
    </section>
  );
}
