import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import V2LandingPage from '@/components/pages/V2LandingPage';

type V2PageProps = {
  params: Promise<{ locale: string }>;
};

function isSupportedLocale(locale: string) {
  return locale === 'en' || locale === 'zh';
}

export async function generateMetadata({
  params,
}: V2PageProps): Promise<Metadata> {
  const { locale } = await params;

  if (!isSupportedLocale(locale)) {
    notFound();
  }

  const isZh = locale === 'zh';

  return {
    title: isZh
      ? 'Aqina V2｜黄梨酵素滴鸡精｜轻负担详情页'
      : 'Aqina V2 | Pineapple Enzyme Chicken Essence Singapore',
    description: isZh
      ? 'Aqina V2 黄梨酵素滴鸡精详情页，以暖米金视觉呈现清爽汤感、即热即饮、真实场景与日常补养套餐。'
      : 'Aqina V2 presents pineapple enzyme chicken essence with a lighter warm routine, clean soup-like taste, real usage scenes, and Singapore delivery.',
    alternates: {
      canonical: `/v2/${locale}`,
      languages: {
        en: '/v2/en',
        zh: '/v2/zh',
      },
    },
  };
}

export default async function V2Page({ params }: V2PageProps) {
  const { locale } = await params;

  if (!isSupportedLocale(locale)) {
    notFound();
  }

  return <V2LandingPage />;
}
