import type { Metadata } from "next";
import { notFound } from "next/navigation";

import V3MaternityLandingPage from "@/components/pages/V3MaternityLandingPage";

type V3PageProps = {
  params: Promise<{ locale: string }>;
};

function isSupportedLocale(locale: string) {
  return locale === "en" || locale === "zh";
}

export async function generateMetadata({
  params,
}: V3PageProps): Promise<Metadata> {
  const { locale } = await params;

  if (!isSupportedLocale(locale)) {
    notFound();
  }

  const isZh = locale === "zh";

  return {
    title: isZh
      ? "Aqina V3｜孕产专属黄梨酵素滴鸡精"
      : "Aqina V3 | Maternity Pineapple Enzyme Chicken Essence",
    description: isZh
      ? "Aqina V3 孕产专属页面，以清爽果香、零油清汤感与温柔日常补给，陪伴怀孕与月子阶段的妈妈。"
      : "Aqina V3 maternity landing page for pineapple enzyme chicken essence, made for clean, light, easy-to-sip nourishment during pregnancy and confinement routines.",
    alternates: {
      canonical: `/v3/${locale}`,
      languages: {
        en: "/v3/en",
        zh: "/v3/zh",
      },
    },
  };
}

export default async function V3Page({ params }: V3PageProps) {
  const { locale } = await params;

  if (!isSupportedLocale(locale)) {
    notFound();
  }

  return <V3MaternityLandingPage />;
}
