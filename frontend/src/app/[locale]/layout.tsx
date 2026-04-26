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
  title: "Aqina 滴鸡精｜黄梨酵素滴鸡精｜轻负担日常补养",
  description:
    "Aqina 黄梨酵素滴鸡精，以清爽汤感、温热即饮与暖米金高级详情页呈现日常可持续的轻负担补养选择。",
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
