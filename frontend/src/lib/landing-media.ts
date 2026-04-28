import { IMAGES } from '@/lib/image-utils';

const brandImages = [
  '/brands/resorts-world-sentosa.png',
  '/brands/jaya-grocer.png',
  '/brands/aeon.svg',
  '/brands/lotuss.svg',
  '/brands/village-grocer.jpg',
];

const trustImages = [
  IMAGES.trust.complianceBadge,
  IMAGES.trust.halalBadge,
  IMAGES.trust.veterinaryBadge,
];

const productImages = [
  IMAGES.products.box1,
  IMAGES.products.box2,
  IMAGES.products.box4,
  IMAGES.products.box6,
];

export const greenLandingMedia = [
  IMAGES.hero,
  '/story/pineapple-craft.webp',
  '/story/pure-essence-bowl.webp',
  '/story/family-care.webp',
  '/story/value-cta-product.webp',
  ...IMAGES.ugc.reviews,
  ...trustImages,
  ...brandImages,
  ...productImages,
];

export const v2LandingMedia = [
  '/v2/aqina-v2-hero-product-real.webp',
  '/v2/aqina-v2-pineapple-farm.webp',
  '/v2/aqina-v2-golden-essence.webp',
  '/v2/aqina-v2-family-care.webp',
  '/ugc/sg-young-indian-office-man.webp',
  '/ugc/sg-middle-aged-malay-woman.webp',
  '/ugc/sg-teenage-chinese-student.webp',
  '/story/family-care.webp',
  '/ugc/morning-kitchen.jpg',
  '/ugc/home-study.jpg',
  '/ugc/yoga-studio.jpg',
  '/ugc/sg-middle-aged-chinese-man.webp',
  '/ugc/sg-young-indian-home-woman.webp',
  ...trustImages,
  ...brandImages,
  ...productImages,
];

export const v3MaternityLandingMedia = [
  '/v3/maternity-hero.jpg',
  '/v3/empathy-nausea.jpg',
  '/v3/empathy-fatigue.jpg',
  '/v3/light-ritual.jpg',
  '/v3/ugc-new-mum.jpg',
  '/v3/ugc-morning-mum.jpg',
  '/v3/ugc-working-mum.jpg',
  '/v3/ugc-partner-care.jpg',
  ...trustImages,
  ...productImages,
];
