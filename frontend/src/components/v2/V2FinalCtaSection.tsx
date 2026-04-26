"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { ArrowRight, MessageCircle } from "lucide-react";
import { getWhatsAppHref } from "@/lib/site-config";

export default function V2FinalCtaSection() {
  const t = useTranslations("Index.v2.finalCta");

  return (
    <section id="v2-final-cta" className="bg-[#fff7e8] py-16 md:py-24">
      <div className="section-shell">
        <div className="grid overflow-hidden rounded-lg border border-[#d9b46b] bg-[#1b130c] text-[#fff7e8] shadow-[0_24px_70px_rgba(91,57,24,0.2)] lg:grid-cols-[1.02fr_0.98fr]">
          <div className="flex flex-col justify-center gap-6 p-7 md:p-10">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#e9c371]">
              {t("eyebrow")}
            </p>
            <div className="space-y-4">
              <h2 className="font-heading text-4xl font-semibold leading-tight md:text-6xl">
                {t("title")}
              </h2>
              <p className="max-w-2xl text-base leading-8 text-[#f5dfb7]/82">
                {t("body")}
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <a
                id="v2-final-products-cta"
                href="#products"
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[#e9c371] px-6 text-sm font-bold text-[#1b130c] hover:bg-[#f5d88f]"
              >
                <span>{t("productsCta")}</span>
                <ArrowRight size={17} />
              </a>
              <a
                id="v2-final-whatsapp-cta"
                href={getWhatsAppHref(t("whatsappMessage"))}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-[#e9c371]/42 px-6 text-sm font-bold text-[#fff7e8] hover:bg-white/10"
              >
                <MessageCircle size={17} />
                <span>{t("whatsappCta")}</span>
              </a>
            </div>
          </div>

          <div className="relative min-h-80">
            <Image
              src="/v2/aqina-v2-family-care.webp"
              alt={t("imageAlt")}
              fill
              sizes="(max-width: 1024px) 92vw, 44vw"
              className="object-cover"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
