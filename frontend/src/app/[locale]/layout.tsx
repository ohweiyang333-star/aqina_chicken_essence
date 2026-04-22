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
  title: "Aqina Singapore 滴鸡精｜Halal 认证・2-3天送达・真实口碑",
  description:
    "Aqina 新加坡官方页面：满额免邮活动进行中，Halal 认证，2-3 天送达，50,000+ 销量与 4.9★ 用户评分，适合孕期、术后与高强度职场恢复。",
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
