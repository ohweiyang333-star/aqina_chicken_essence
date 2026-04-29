import type { Metadata } from "next";
import { notFound } from "next/navigation";

import V4CulinaryLandingPage from "@/components/pages/V4CulinaryLandingPage";
import {
  v4CulinaryContent,
  type V4Locale,
} from "@/lib/v4-culinary-content";

type V4PageProps = {
  params: Promise<{ locale: string }>;
};

function isSupportedLocale(locale: string): locale is V4Locale {
  return locale === "en" || locale === "zh";
}

export async function generateMetadata({
  params,
}: V4PageProps): Promise<Metadata> {
  const { locale } = await params;

  if (!isSupportedLocale(locale)) {
    notFound();
  }

  const content = v4CulinaryContent[locale];

  return {
    title: content.meta.title,
    description: content.meta.description,
    alternates: {
      canonical: `/v4/${locale}`,
      languages: {
        en: "/v4/en",
        zh: "/v4/zh",
      },
    },
  };
}

export default async function V4Page({ params }: V4PageProps) {
  const { locale } = await params;

  if (!isSupportedLocale(locale)) {
    notFound();
  }

  return <V4CulinaryLandingPage locale={locale} />;
}
