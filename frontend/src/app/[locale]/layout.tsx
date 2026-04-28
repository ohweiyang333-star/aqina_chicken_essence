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
      ? "Aqina 阿其纳滴鸡精｜好吸收、轻负担的每日补养"
      : "Aqina Premium Chicken Essence Singapore | Clean Daily Recovery",
    description: isZh
      ? "Aqina 黄梨酵素滴鸡精，聚焦好吸收、轻负担与每日可持续的温热补养，支持新加坡家庭、恢复期与日常元气管理。"
      : "Aqina pineapple enzyme chicken essence is made for clean absorption, gentle daily recovery, and easy warm nourishment for Singapore families.",
    alternates: {
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
