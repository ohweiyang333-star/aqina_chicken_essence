"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { HeartHandshake, Users } from "lucide-react";
import V2SectionHeading from "./V2SectionHeading";

interface AudienceItem {
  title: string;
  body: string;
  image: string;
  alt: string;
}

export default function V2AudienceSection() {
  const t = useTranslations("Index.v2.audience");
  const items = t.raw("items") as AudienceItem[];

  return (
    <section id="v2-audience" className="bg-[#f8ecd5] py-16 md:py-24">
      <div className="section-shell space-y-10">
        <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <V2SectionHeading
            eyebrow={t("eyebrow")}
            title={t("title")}
            body={t("body")}
          />
          <div className="inline-flex w-fit items-center gap-2 rounded-lg border border-[#d9b46b] bg-white/72 px-4 py-3 text-sm font-bold text-[#6d451d]">
            <Users size={18} />
            <span>{t("badge")}</span>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {items.map((item) => (
            <article
              key={item.title}
              className="overflow-hidden rounded-lg border border-[#dcc08c] bg-white shadow-[0_14px_36px_rgba(91,57,24,0.07)]"
            >
              <div className="relative aspect-[4/3]">
                <Image
                  src={item.image}
                  alt={item.alt}
                  fill
                  sizes="(max-width: 768px) 92vw, (max-width: 1024px) 44vw, 22vw"
                  className="object-cover"
                />
              </div>
              <div className="space-y-3 p-5">
                <div className="flex items-center gap-2 text-[#9b6b1f]">
                  <HeartHandshake size={18} />
                  <h3 className="text-lg font-bold text-[#23170d]">
                    {item.title}
                  </h3>
                </div>
                <p className="text-sm leading-7 text-[#6f5a43]">{item.body}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
