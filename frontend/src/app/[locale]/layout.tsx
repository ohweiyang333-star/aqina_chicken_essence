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
  title: "Aqina Ancient Traditional Chicken Essence | 阿其纳古法滴鸡精",
  description: "Authentic Malaysian recipe chicken essence. 100% natural, no additives. High protein and amino acids for your family vitality.",
  keywords: ["Chicken Essence", "滴鸡精", "Aqina", "Health Supplement", "Singapore"],
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
