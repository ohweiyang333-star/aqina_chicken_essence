import { ReactNode } from 'react';
import { notFound } from 'next/navigation';
import { NextIntlClientProvider } from 'next-intl';

import Header from '@/components/Header';
import WhatsAppButton from '@/components/WhatsAppButton';
import enMessages from '../../../../messages/en.json';
import zhMessages from '../../../../messages/zh.json';

const messagesByLocale = {
  en: enMessages,
  zh: zhMessages,
};

type SupportedLocale = keyof typeof messagesByLocale;

function isSupportedLocale(locale: string): locale is SupportedLocale {
  return locale === 'en' || locale === 'zh';
}

export function generateStaticParams() {
  return [{ locale: 'en' }, { locale: 'zh' }];
}

export default async function V2LocaleLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  if (!isSupportedLocale(locale)) {
    notFound();
  }

  return (
    <NextIntlClientProvider locale={locale} messages={messagesByLocale[locale]}>
      <div className="min-h-full flex flex-col bg-background-dark text-text-light font-body">
        <Header />
        {children}
        <WhatsAppButton />
      </div>
    </NextIntlClientProvider>
  );
}
