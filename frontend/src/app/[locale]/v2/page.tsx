import type { Metadata } from 'next';
import V2LandingPage from '@/components/pages/V2LandingPage';

export const metadata: Metadata = {
  title: 'Aqina V2｜黄梨酵素滴鸡精｜轻负担详情页',
  description:
    'Aqina V2 黄梨酵素滴鸡精详情页，以暖米金视觉呈现清爽汤感、即热即饮、真实场景与日常补养套餐。',
};

export default function V2Page() {
  return <V2LandingPage />;
}
