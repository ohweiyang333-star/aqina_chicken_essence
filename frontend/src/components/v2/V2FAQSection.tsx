"use client";

import { useTranslations } from "next-intl";
import V2SectionHeading from "./V2SectionHeading";
import { MotionItem, StaggerGroup } from "./V2Motion";

interface FAQItem {
  question: string;
  answer: string;
}

export default function V2FAQSection() {
  const t = useTranslations("Index.v2.faq");
  const items = t.raw("items") as FAQItem[];

  return (
    <section id="v2-faq" className="bg-[#fffaf1] py-16 md:py-24">
      <div className="section-shell space-y-8">
        <V2SectionHeading
          eyebrow={t("eyebrow")}
          title={t("title")}
          body={t("body")}
          align="center"
        />

        <StaggerGroup
          className="mx-auto grid max-w-4xl gap-3"
          staggerChildren={0.08}
        >
          {items.map((item) => (
            <MotionItem
              as="article"
              key={item.question}
              className="rounded-lg border border-[#dcc08c] bg-white px-5 py-5 shadow-[0_12px_30px_rgba(91,57,24,0.06)]"
              y={16}
            >
              <h3 className="text-base font-bold leading-7 text-[#23170d]">
                {item.question}
              </h3>
              <p className="mt-2 text-sm leading-7 text-[#6f5a43]">{item.answer}</p>
            </MotionItem>
          ))}
        </StaggerGroup>
      </div>
    </section>
  );
}
