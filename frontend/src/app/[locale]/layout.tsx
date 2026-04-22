import type { Metadata } from "next";
import { Cormorant_Garamond, Plus_Jakarta_Sans } from "next/font/google";
import { ReactNode } from "react";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import "../globals.css";

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  variable: "--font-cormorant",
  weight: ["600", "700"],
});

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "Aqina 滴鸡精｜术后产后恢复期补养方案｜Halal认证・2-3天送达",
  description:
    "面向术后与产后恢复阶段的日常补养方案：聚焦轻负担吸收与家庭照护场景，Halal 认证，2-3 天送达，支持 7/14/28/42 天周期化安排。",
  keywords: [
    "Aqina Singapore",
    "鸡精",
    "滴鸡精",
    "Halal Certified",
    "Free Shipping Singapore",
    "2-3 days delivery",
    "UGC Reviews",
  ],
};

import Header from "@/components/Header";
import WhatsAppButton from "@/components/WhatsAppButton";

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
    <html lang={locale} className={`${cormorant.variable} ${jakarta.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-background-dark text-text-light font-body">
        <NextIntlClientProvider locale={locale} messages={messages}>
          <Header />
          {children}
          <WhatsAppButton />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
