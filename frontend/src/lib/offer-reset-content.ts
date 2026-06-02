import type { DisplayProduct } from './product-display';

export type OfferResetLocale = 'en' | 'zh';

export interface OfferResetGift {
  id: string;
  name: string;
  weight: string;
  image: string;
  alt: Record<OfferResetLocale, string>;
}

export interface OfferResetProofItem {
  id: string;
  title: Record<OfferResetLocale, string>;
  body: Record<OfferResetLocale, string>;
  image?: string;
  alt?: Record<OfferResetLocale, string>;
}

export interface OfferResetQaItem {
  question: Record<OfferResetLocale, string>;
  answer: Record<OfferResetLocale, string>;
}

export const OFFER_RESET_PRODUCTS: DisplayProduct[] = [
  {
    id: 'pack1',
    name: 'Aqina 纯鸡精 1盒',
    price: 47.9,
    image: '/v2/aqina-v2-hero-product-real.webp',
    label: '7 PACKS x 60g',
    badge: '1盒试喝',
  },
  {
    id: 'pack2',
    name: 'Aqina 纯鸡精 2盒',
    price: 79.8,
    image: '/v2/aqina-v2-hero-product-real.webp',
    label: '14 PACKS x 60g + French Poulet Cut Part 五选一',
    badge: '推荐：SGD39.90/盒 + 赠品',
    popular: true,
  },
];

export const OFFER_RESET_GIFTS: OfferResetGift[] = [
  {
    id: 'joint-wing',
    name: 'French Poulet 3 Joint Wing',
    weight: '500g',
    image: '/french-poulet-gift/chicken-wing.jpg',
    alt: {
      en: 'French Poulet 3 Joint Wing 500g gift option',
      zh: 'French Poulet 3 Joint Wing 500g 赠品选项',
    },
  },
  {
    id: 'minced',
    name: 'French Poulet Minced',
    weight: '400g',
    image: '/french-poulet-gift/minced.png',
    alt: {
      en: 'French Poulet Minced 400g gift option',
      zh: 'French Poulet Minced 400g 赠品选项',
    },
  },
  {
    id: 'boneless-breast',
    name: 'French Poulet Boneless Breast',
    weight: '350g',
    image: '/french-poulet-gift/boneless-breast.png',
    alt: {
      en: 'French Poulet Boneless Breast 350g gift option',
      zh: 'French Poulet Boneless Breast 350g 赠品选项',
    },
  },
  {
    id: 'whole-leg',
    name: 'French Poulet Whole Leg',
    weight: '400g',
    image: '/french-poulet-gift/whole-leg.jpg',
    alt: {
      en: 'French Poulet Whole Leg 400g gift option',
      zh: 'French Poulet Whole Leg 400g 赠品选项',
    },
  },
  {
    id: 'half-chicken',
    name: 'French Poulet Half Chicken Cut 4 Pieces',
    weight: '500g',
    image: '/french-poulet-gift/half-chicken-4-cut.jpg',
    alt: {
      en: 'French Poulet Half Chicken Cut 4 Pieces 500g gift option',
      zh: 'French Poulet Half Chicken Cut 4 Pieces 500g 赠品选项',
    },
  },
];

export function normalizeOfferResetLocale(locale: string): OfferResetLocale {
  return locale === 'zh' ? 'zh' : 'en';
}

export function getOfferResetWhatsAppMessage(
  locale: string,
  intent: 'confirm' | 'pack1' | 'pack2' = 'confirm',
) {
  const safeLocale = normalizeOfferResetLocale(locale);

  if (safeLocale === 'zh') {
    if (intent === 'pack1') {
      return 'Hi Aqina SG，我想先确认 Aqina 纯鸡精 1盒 SGD47.90 适不适合我。';
    }
    if (intent === 'pack2') {
      return 'Hi Aqina SG，我想确认 Aqina 纯鸡精 2盒 SGD79.80 的 French Poulet Cut Part 赠品可以选哪一款。';
    }
    return 'Hi Aqina SG，我想确认 Aqina 纯鸡精 1盒 / 2盒配套。请帮我确认 2盒 SGD79.80 的 French Poulet Cut Part 赠品可以选哪一款。';
  }

  if (intent === 'pack1') {
    return 'Hi Aqina SG, I want to confirm if the 1-box Aqina Pure Chicken Essence at SGD47.90 suits me.';
  }
  if (intent === 'pack2') {
    return 'Hi Aqina SG, I want to confirm the 2-box Aqina Pure Chicken Essence offer at SGD79.80 and the French Poulet Cut Part gift choice.';
  }
  return 'Hi Aqina SG, I want to confirm whether I should choose the 1-box or 2-box Aqina Pure Chicken Essence offer, and which French Poulet Cut Part gift is available for the 2-box offer.';
}

export function getOfferResetCopy(locale: string) {
  const safeLocale = normalizeOfferResetLocale(locale);

  return safeLocale === 'zh'
    ? {
        heroEyebrow: 'Aqina 纯鸡精｜6月新版配套',
        heroTitle: '不是普通瓶装鸡精的价格比较，是 Aqina 纯鸡精的原汤等级。',
        heroBody: '1盒 SGD47.90。2盒 SGD79.80，等于每盒 SGD39.90，并送 French Poulet Cut Part 五选一。',
        primaryCta: 'WhatsApp 确认 1盒 / 2盒和赠品',
        secondaryCta: '直接 PayNow 上传收据下单',
        productProofTitle: '先看真实产品和购买证明，再决定配套。',
        productProofBody:
          '用真实包装、French Poulet 赠品、PayNow/WhatsApp 成交流程、Aqina farm、MD2 黄梨酵素鸡、7天慢炼、Halal、无添加建立信任。',
        offersTitle: '这次只保留 1盒和 2盒',
        giftsTitle: '2盒送 French Poulet Cut Part，五选一',
        giftsBody: '赠品库存由客服在 WhatsApp 确认。赠品不能大过主产品，主角仍然是 Aqina 纯鸡精。',
        qaTitle: '购买前 Q&A',
        reviewTitle: '真实评价待导入',
        reviewBody: '当前区块先保留真实评价槽位。等客服收集到授权反馈后，再导入真实文字、截图或买家秀。',
        finalTitle: '想先确认，走 WhatsApp；已经决定，走 PayNow。',
      }
    : {
        heroEyebrow: 'Aqina Pure Chicken Essence | June offer reset',
        heroTitle: 'Not an ordinary bottled chicken essence price comparison.',
        heroBody:
          '1 box at SGD47.90. 2 boxes at SGD79.80, equal to SGD39.90 per box, with one French Poulet Cut Part gift choice.',
        primaryCta: 'Confirm 1 box / 2 boxes and gift on WhatsApp',
        secondaryCta: 'PayNow and upload receipt directly',
        productProofTitle: 'Check product proof before choosing a pack.',
        productProofBody:
          'Build trust with real packaging, French Poulet gift photos, PayNow / WhatsApp order path, Aqina farm, MD2 pineapple chicken, 7-day slow extraction, Halal, and no-additive proof.',
        offersTitle: 'This reset keeps only 1 box and 2 boxes',
        giftsTitle: 'Buy 2 boxes and choose one French Poulet Cut Part',
        giftsBody:
          'Support confirms available gift stock on WhatsApp. The gift supports the offer, while Aqina Pure Chicken Essence remains the main product.',
        qaTitle: 'Buying Q&A',
        reviewTitle: 'Real reviews pending import',
        reviewBody:
          'This section keeps real-ready review slots. Import real text, screenshots, or customer photos only after support collects approved feedback.',
        finalTitle: 'Need confirmation? Use WhatsApp. Ready to order? Use PayNow.',
      };
}
