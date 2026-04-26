"use client";

import { useTranslations } from "next-intl";
import { CheckCircle2, MinusCircle, Scale } from "lucide-react";
import V2SectionHeading from "./V2SectionHeading";

interface ComparisonItem {
  label: string;
  ordinary: string;
  aqina: string;
}

export default function V2ComparisonSection() {
  const t = useTranslations("Index.v2.comparison");
  const items = t.raw("items") as ComparisonItem[];

  return (
    <section id="v2-comparison" className="bg-[#fff7e8] py-16 md:py-24">
      <div className="section-shell">
        <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <V2SectionHeading
            eyebrow={t("eyebrow")}
            title={t("title")}
            body={t("body")}
          />

          <div className="overflow-hidden rounded-lg border border-[#e2c894] bg-white shadow-[0_18px_50px_rgba(91,57,24,0.08)]">
            <div className="grid grid-cols-[0.84fr_1fr_1fr] border-b border-[#ead3a7] bg-[#f7e8c9] text-xs font-bold uppercase tracking-[0.14em] text-[#6d451d]">
              <div className="flex items-center gap-2 px-4 py-4">
                <Scale size={15} />
                <span>{t("criteriaLabel")}</span>
              </div>
              <div className="px-4 py-4">{t("ordinaryTitle")}</div>
              <div className="px-4 py-4">{t("aqinaTitle")}</div>
            </div>

            {items.map((item) => (
              <div
                key={item.label}
                className="grid grid-cols-1 border-b border-[#f0dfbd] last:border-b-0 md:grid-cols-[0.84fr_1fr_1fr]"
              >
                <div className="bg-[#fffaf1] px-4 py-5 text-sm font-bold text-[#402916]">
                  {item.label}
                </div>
                <div className="flex gap-3 px-4 py-5 text-sm leading-7 text-[#7b6958]">
                  <MinusCircle
                    size={18}
                    className="mt-1 shrink-0 text-[#a88a63]"
                  />
                  <span>{item.ordinary}</span>
                </div>
                <div className="flex gap-3 bg-[#fff7e8] px-4 py-5 text-sm font-semibold leading-7 text-[#4f351e]">
                  <CheckCircle2
                    size={18}
                    className="mt-1 shrink-0 text-[#9b6b1f]"
                  />
                  <span>{item.aqina}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
