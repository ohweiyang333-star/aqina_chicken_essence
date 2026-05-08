import { IMAGES } from './image-utils';

export interface DisplayProduct {
  id: string;
  name: string;
  price: number;
  image: string;
  label: string;
  popular?: boolean;
  badge?: string | null;
}

export const FIXED_PRODUCT_IMAGES = {
  pack1: IMAGES.products.box1,
  pack2: IMAGES.products.box2,
  pack4: IMAGES.products.box4,
  pack6: IMAGES.products.box6,
} as const;

export type FixedPackKey = keyof typeof FIXED_PRODUCT_IMAGES;

function resolvePackKeyFromHints(hints: string[], price: number): FixedPackKey {
  const text = hints.join(' ').toLowerCase();

  if (
    text.includes('42') ||
    text.includes('6盒') ||
    text.includes('6 box') ||
    text.includes('six') ||
    text.includes('六')
  ) {
    return 'pack6';
  }

  if (
    text.includes('28') ||
    text.includes('4盒') ||
    text.includes('4 box') ||
    text.includes('four') ||
    text.includes('四')
  ) {
    return 'pack4';
  }

  if (
    text.includes('14') ||
    text.includes('2盒') ||
    text.includes('2 box') ||
    text.includes('two') ||
    text.includes('二') ||
    text.includes('两')
  ) {
    return 'pack2';
  }

  if (
    text.includes('7') ||
    text.includes('1盒') ||
    text.includes('1 box') ||
    text.includes('one') ||
    text.includes('一')
  ) {
    return 'pack1';
  }

  if (price >= 200) return 'pack6';
  if (price >= 130) return 'pack4';
  if (price >= 60) return 'pack2';
  return 'pack1';
}

export function resolveFixedPackKeyByMeta(options: {
  id?: string;
  packSize?: string;
  nameEn?: string;
  nameZh?: string;
  price?: number;
}): FixedPackKey {
  return resolvePackKeyFromHints(
    [
      options.id ?? '',
      options.packSize ?? '',
      options.nameEn ?? '',
      options.nameZh ?? '',
    ],
    Number(options.price ?? 0),
  );
}

export function resolveFixedProductImageByMeta(options: {
  id?: string;
  packSize?: string;
  nameEn?: string;
  nameZh?: string;
  price?: number;
}): string {
  const packKey = resolveFixedPackKeyByMeta(options);

  return FIXED_PRODUCT_IMAGES[packKey];
}
