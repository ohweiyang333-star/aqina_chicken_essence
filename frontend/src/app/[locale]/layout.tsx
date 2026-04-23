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
  title: "Aqina 滴鸡精｜零负担吸收的纯粹能量｜黄梨酵素滴鸡精",
  description:
    "给身体最纯粹的能量，从零负担吸收开始。Aqina 黄梨酵素滴鸡精，聚焦好吸收、轻负担与每日可持续的温热补养。",
  icons: {
    icon: [
      { url: "/icon.png", type: "image/png", sizes: "512x512" },
      { url: "/favicon.ico", type: "image/x-icon" },
    ],
    shortcut: ["/favicon.ico"],
    apple: ["/apple-icon.png"],
  },
  keywords: [
    "Aqina Singapore",
    "鸡精",
    "滴鸡精",
    "Halal Certified",
    "Free Shipping Singapore",
    "2-3 days delivery",
    "Customer Reviews",
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
