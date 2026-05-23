"use client";

import Image from "next/image";
import { useLocale, useTranslations } from "next-intl";
import {
  ArrowRight,
  Camera,
  CheckCircle2,
  CreditCard,
  MessageCircle,
  Package,
  Send,
  Soup,
  Truck,
} from "lucide-react";

import { getMessengerHref, getWhatsAppHref } from "@/lib/site-config";
import { trackLandingFunnelEvent } from "@/lib/marketing-analytics";
import V2SectionHeading from "./V2SectionHeading";
import { MotionItem, Reveal, StaggerGroup } from "./V2Motion";

interface PackageOption {
  id: string;
  badge: string;
  title: string;
  price: string;
  subtitle: string;
  body: string;
  points: string[];
}

interface FaqItem {
  title: string;
  body: string;
}

const faqIcons = [Truck, CreditCard, Camera, MessageCircle] as const;

export default function V2BofuOrderSection() {
  const t = useTranslations("Index.v2.bofu");
  const locale = useLocale();
  const packages = t.raw("packages") as PackageOption[];
  const faqItems = t.raw("faqItems") as FaqItem[];
  const tasteBullets = t.raw("tasteBullets") as string[];
  const proofPoints = t.raw("proofPoints") as string[];
  const isZh = locale === "zh";

  const askTwoBoxMessage = isZh
    ? "Hi Aqina SG，我想问 2盒 SGD75 免运配套，麻烦帮我确认适不适合。"
    : "Hi Aqina SG, I want to ask about the 2-box SGD 75 free delivery pack. Please help me confirm if it suits me.";
  const orderMessage = isZh
    ? "Hi Aqina SG，我想下单 Aqina 纯鸡精，请帮我确认配套、PayNow 和配送。"
    : "Hi Aqina SG, I would like to order Aqina chicken essence. Please help me confirm the pack, PayNow, and delivery.";

  const handleCtaClick = (source: string, destination: string) => {
    trackLandingFunnelEvent("whatsapp_cta_click", {
      source,
      destination,
    });
  };

  return (
    <section
      id="v2-bofu-order"
      className="bg-[#fffaf1] py-16 text-[#23170d] md:py-24"
    >
      <div className="section-shell space-y-10">
        <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
          <V2SectionHeading
            eyebrow={t("eyebrow")}
            title={t("title")}
            body={t("body")}
          />
          <Reveal
            as="aside"
            className="rounded-lg border border-[#d8b774] bg-[#f8ecd5] p-5 text-sm leading-7 text-[#5f492f] shadow-[0_18px_46px_rgba(91,57,24,0.08)]"
            y={18}
          >
            <p className="font-bold text-[#23170d]">{t("decisionTitle")}</p>
            <p className="mt-2">{t("decisionBody")}</p>
          </Reveal>
        </div>

        <StaggerGroup
          className="grid gap-4 md:grid-cols-3"
          staggerChildren={0.08}
        >
          {packages.map((option) => (
            <MotionItem
              as="article"
              key={option.id}
              className={[
                "flex h-full flex-col rounded-lg border bg-white p-5 shadow-[0_16px_38px_rgba(91,57,24,0.08)]",
                option.id === "pack2"
                  ? "border-[#9b6b1f] ring-2 ring-[#e7c779]"
                  : "border-[#dcc08c]",
              ].join(" ")}
              y={16}
            >
              <div className="flex items-start justify-between gap-3">
                <span className="rounded-md bg-[#f2dba8] px-3 py-1 text-xs font-bold uppercase tracking-[0.12em] text-[#7c531c]">
                  {option.badge}
                </span>
                <Package size={20} className="shrink-0 text-[#9b6b1f]" />
              </div>
              <h3 className="mt-5 text-xl font-bold leading-7 text-[#23170d]">
                {option.title}
              </h3>
              <p className="mt-2 font-heading text-3xl font-semibold leading-tight text-[#20150c]">
                {option.price}
              </p>
              <p className="mt-2 text-sm font-semibold leading-6 text-[#7c531c]">
                {option.subtitle}
              </p>
              <p className="mt-4 text-sm leading-7 text-[#6f5a43]">
                {option.body}
              </p>
              <ul className="mt-5 space-y-2 border-t border-[#e7c779] pt-5">
                {option.points.map((point) => (
                  <li
                    key={point}
                    className="flex items-start gap-2 text-sm leading-6 text-[#5f492f]"
                  >
                    <CheckCircle2
                      size={17}
                      className="mt-1 shrink-0 text-[#9b6b1f]"
                    />
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </MotionItem>
          ))}
        </StaggerGroup>

        <div className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <Reveal
            as="figure"
            className="relative min-h-[24rem] overflow-hidden rounded-lg border border-[#d8b774] bg-[#f2dba8] shadow-[0_22px_60px_rgba(91,57,24,0.11)]"
            y={18}
          >
            <Image
              src="/v2/aqina-v2-golden-essence.webp"
              alt={t("tasteImageAlt")}
              fill
              sizes="(max-width: 1024px) 92vw, 48vw"
              className="object-cover object-center"
            />
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#23170d]/86 via-[#23170d]/48 to-transparent p-5 text-[#fffaf1]">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#f0c66e]">
                {t("tasteEyebrow")}
              </p>
              <h3 className="mt-2 text-2xl font-bold leading-8">
                {t("tasteTitle")}
              </h3>
            </div>
          </Reveal>

          <div className="grid gap-4">
            <Reveal
              as="article"
              className="rounded-lg border border-[#d8b774] bg-white p-5 shadow-[0_16px_38px_rgba(91,57,24,0.07)]"
              y={18}
            >
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#f2dba8] text-[#7c531c]">
                  <Soup size={20} />
                </span>
                <div>
                  <h3 className="text-lg font-bold text-[#23170d]">
                    {t("tasteRiskTitle")}
                  </h3>
                  <p className="text-sm leading-6 text-[#6f5a43]">
                    {t("tasteRiskBody")}
                  </p>
                </div>
              </div>
              <ul className="mt-5 grid gap-2">
                {tasteBullets.map((item) => (
                  <li
                    key={item}
                    className="flex items-start gap-2 text-sm leading-6 text-[#5f492f]"
                  >
                    <CheckCircle2
                      size={17}
                      className="mt-1 shrink-0 text-[#9b6b1f]"
                    />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </Reveal>

            <StaggerGroup className="grid gap-3 sm:grid-cols-3" staggerChildren={0.06}>
              {proofPoints.map((item) => (
                <MotionItem
                  as="p"
                  key={item}
                  className="rounded-lg border border-[#dcc08c] bg-[#fff7e8] px-4 py-4 text-sm font-bold leading-6 text-[#5f492f]"
                  y={14}
                >
                  {item}
                </MotionItem>
              ))}
            </StaggerGroup>
          </div>
        </div>

        <StaggerGroup
          className="grid gap-3 md:grid-cols-4"
          staggerChildren={0.07}
        >
          {faqItems.map((item, index) => {
            const Icon = faqIcons[index % faqIcons.length];

            return (
              <MotionItem
                as="article"
                key={item.title}
                className="rounded-lg border border-[#dcc08c] bg-white px-5 py-5 shadow-[0_12px_30px_rgba(91,57,24,0.06)]"
                y={16}
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#f2dba8] text-[#7c531c]">
                  <Icon size={19} />
                </span>
                <h3 className="mt-4 text-base font-bold leading-7 text-[#23170d]">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-7 text-[#6f5a43]">
                  {item.body}
                </p>
              </MotionItem>
            );
          })}
        </StaggerGroup>

        <Reveal
          as="aside"
          className="rounded-lg border border-[#9b6b1f] bg-[#23170d] p-5 text-[#fffaf1] shadow-[0_22px_60px_rgba(35,23,13,0.24)] md:p-6"
          y={18}
        >
          <div className="grid gap-5 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#f0c66e]">
                {t("ctaEyebrow")}
              </p>
              <h3 className="mt-2 text-2xl font-bold leading-8 md:text-3xl">
                {t("ctaTitle")}
              </h3>
              <p className="mt-2 text-sm leading-7 text-[#e8d7b9]">
                {t("ctaBody")}
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <a
                id="v2-bofu-ask-2box-cta"
                href={getWhatsAppHref(askTwoBoxMessage)}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => handleCtaClick("v2_bofu_ask_2box", "whatsapp")}
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[#f0c66e] px-4 text-center text-sm font-bold text-[#23170d] transition hover:-translate-y-0.5 hover:bg-[#ffd986]"
              >
                <ArrowRight size={17} />
                <span>{t("askCta")}</span>
              </a>
              <a
                id="v2-bofu-whatsapp-order-cta"
                href={getWhatsAppHref(orderMessage)}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => handleCtaClick("v2_bofu_order_whatsapp", "whatsapp")}
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-[#f0c66e]/70 bg-white/8 px-4 text-center text-sm font-bold text-[#fffaf1] transition hover:-translate-y-0.5 hover:bg-white/14"
              >
                <MessageCircle size={17} />
                <span>{t("whatsappCta")}</span>
              </a>
              <a
                id="v2-bofu-messenger-cta"
                href={getMessengerHref()}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => handleCtaClick("v2_bofu_messenger", "messenger")}
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-[#f0c66e]/70 bg-white/8 px-4 text-center text-sm font-bold text-[#fffaf1] transition hover:-translate-y-0.5 hover:bg-white/14"
              >
                <Send size={17} />
                <span>{t("messengerCta")}</span>
              </a>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
