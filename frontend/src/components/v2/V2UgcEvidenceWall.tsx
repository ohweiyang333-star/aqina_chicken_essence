"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { BadgeCheck, HelpCircle, MessageCircle } from "lucide-react";
import V2SectionHeading from "./V2SectionHeading";
import { MotionItem, Reveal, StaggerGroup } from "./V2Motion";

interface UGCItem {
  name: string;
  context: string;
  quote: string;
  image?: string;
  alt?: string;
  images?: {
    src: string;
    alt: string;
  }[];
}

interface ReviewSlot {
  label: string;
  title: string;
  body: string;
}

interface QuestionItem {
  question: string;
  answer: string;
}

export default function V2UgcEvidenceWall() {
  const t = useTranslations("Index.v2.ugc");
  const items = t.raw("items") as UGCItem[];
  const reviewSlots = t.raw("reviewSlots") as ReviewSlot[];
  const questions = t.raw("questions") as QuestionItem[];

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
          {items.map((item) => (
            <MotionItem
              as="article"
              key={`${item.name}-${item.context}`}
              className="overflow-hidden rounded-lg border border-[#dcc08c] bg-white shadow-[0_14px_34px_rgba(91,57,24,0.07)] hover:-translate-y-1 hover:shadow-[0_20px_44px_rgba(91,57,24,0.11)]"
              y={24}
            >
              <div className="relative aspect-[4/3]">
                {item.images?.length ? (
                  <div className="grid h-full grid-cols-2 grid-rows-3 gap-1 bg-[#fff2d7] p-1">
                    {item.images.map((image, index) => (
                      <div
                        key={image.src}
                        className={`relative overflow-hidden bg-white ${index === 0 ? "col-span-2" : ""}`}
                      >
                        <Image
                          src={image.src}
                          alt={image.alt}
                          fill
                          sizes="(max-width: 768px) 46vw, (max-width: 1024px) 22vw, 15vw"
                          className="object-cover"
                        />
                      </div>
                    ))}
                  </div>
                ) : item.image ? (
                  <Image
                    src={item.image}
                    alt={item.alt || item.name}
                    fill
                    sizes="(max-width: 768px) 92vw, (max-width: 1024px) 44vw, 30vw"
                    className="object-cover"
                  />
                ) : null}
              </div>
              <div className="space-y-4 p-5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-[#23170d]">{item.name}</h3>
                    <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#9b6b1f]">
                      {item.context}
                    </p>
                  </div>
                  <BadgeCheck
                    size={18}
                    className="shrink-0 text-[#9b6b1f]"
                  />
                </div>
                <p className="text-sm leading-7 text-[#6f5a43]">
                  {item.quote}
                </p>
              </div>
            </MotionItem>
          ))}
        </StaggerGroup>

        <Reveal
          as="div"
          className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]"
          y={18}
        >
          <section
            aria-labelledby="ugc-review-slots-title"
            className="rounded-lg bg-[#23170d] p-6 text-[#fffaf1] shadow-[0_18px_42px_rgba(91,57,24,0.18)]"
          >
            <div className="flex items-start gap-3">
              <MessageCircle className="mt-1 shrink-0 text-[#f3c864]" size={20} />
              <div>
                <h3 id="ugc-review-slots-title" className="text-lg font-black">
                  {t("reviewTitle")}
                </h3>
                <p className="mt-2 text-sm leading-7 text-[#e7d7bc]">{t("reviewBody")}</p>
              </div>
            </div>
            <div className="mt-5 divide-y divide-[#5c482f] border-y border-[#5c482f]">
              {reviewSlots.map((slot) => (
                <div key={slot.title} className="py-4">
                  <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#f3c864]">
                    {slot.label}
                  </p>
                  <h4 className="mt-1 font-bold">{slot.title}</h4>
                  <p className="mt-1 text-sm leading-6 text-[#e7d7bc]">{slot.body}</p>
                </div>
              ))}
            </div>
          </section>

          <section
            aria-labelledby="ugc-qa-title"
            className="rounded-lg border border-[#dcc08c] bg-white p-6 shadow-[0_14px_34px_rgba(91,57,24,0.07)]"
          >
            <div className="flex items-start gap-3">
              <HelpCircle className="mt-1 shrink-0 text-[#9b6b1f]" size={20} />
              <h3 id="ugc-qa-title" className="text-lg font-black text-[#23170d]">
                {t("qaTitle")}
              </h3>
            </div>
            <div className="mt-5 divide-y divide-[#ead7b5] border-y border-[#ead7b5]">
              {questions.map((item) => (
                <div key={item.question} className="py-4">
                  <h4 className="font-bold leading-7 text-[#23170d]">{item.question}</h4>
                  <p className="mt-1 text-sm leading-7 text-[#6f5a43]">{item.answer}</p>
                </div>
              ))}
            </div>
          </section>
        </Reveal>

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
