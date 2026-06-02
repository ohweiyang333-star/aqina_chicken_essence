import type { Metadata } from "next";
import { ReactNode } from "react";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';

import Header from "@/components/Header";
import WhatsAppButton from "@/components/WhatsAppButton";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const isZh = locale === "zh";

  return {
    title: isZh
      ? "Aqina 纯鸡精｜1盒 SGD47.90 / 2盒 SGD79.80｜French Poulet 赠品"
      : "Aqina Pure Chicken Essence | 1 Box SGD47.90 / 2 Boxes SGD79.80",
    description: isZh
      ? "Aqina 纯鸡精新版配套：1盒 SGD47.90，2盒 SGD79.80，等于每盒 SGD39.90，并送 French Poulet Cut Part 五选一。WhatsApp 确认配套与赠品，或直接 PayNow 上传收据下单。"
      : "Aqina Pure Chicken Essence offer reset: 1 box at SGD47.90, 2 boxes at SGD79.80, equal to SGD39.90 per box with one French Poulet Cut Part gift choice. Confirm on WhatsApp or PayNow and upload your receipt directly.",
    alternates: {
      canonical: isZh ? "/zh" : "/en",
      languages: {
        en: "/en",
        zh: "/zh",
      },
    },
  };
}

export default async function LocaleLayout({
  children,
  params
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const messages = await getMessages();

  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <div className="min-h-full flex flex-col bg-background-dark text-text-light font-body">
        <Header />
        {children}
        <WhatsAppButton />
      </div>
    </NextIntlClientProvider>
  );
}
