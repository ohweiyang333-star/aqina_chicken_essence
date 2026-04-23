export function getFirebaseUrl(filename: string) {
  return `https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/${encodeURIComponent(filename)}?alt=media`;
}

export function getFirebaseV2Url(filename: string) {
  return getFirebaseUrl(`V2/${filename}`);
}

export const IMAGE_VERSION = '20260423e';

export function withImageVersion(path: string) {
  // Next.js 16 image optimizer rejects local paths with query params.
  // Keep local image src as clean path to avoid 400 responses in <Image />.
  if (path.startsWith('/')) {
    return path.split('?')[0].split('#')[0];
  }
  return path;
}

export const IMAGES = {
  hero: 'https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/V2%2Fdesign-a-professional-website-hero-banner--use-the%20(1).webp?alt=media&token=19a027d8-a5ce-4fbe-a1d0-be287026e346',
  logo: getFirebaseV2Url('Aqina Farm-Logo (Gold).webp'),
  story: getFirebaseUrl('7天双重蒸煮.jpg'),
  trust: {
    complianceBadge: getFirebaseV2Url('HACCP GMP ISO 认证 Logo.png'),
    halalBadge: getFirebaseV2Url('Image 1.png'),
    veterinaryBadge: getFirebaseV2Url('Image 3.png'),
  },
  products: {
    box1: getFirebaseV2Url('clean-product-photography-for-a-landing-page--exac (3).webp'),
    box2: getFirebaseV2Url('clean-product-photography-for-a-landing-page--exac (2).webp'),
    box4: getFirebaseV2Url('clean-product-photography-for-a-landing-page--exac.webp'),
    box6: getFirebaseV2Url('clean-product-photography-for-a-landing-page--exac (1).webp'),
    boxMain: getFirebaseV2Url('clean-product-photography-for-a-landing-page--exac (3).webp'),
  },
  ugc: {
    reviews: [
      getFirebaseV2Url('a-warm-and-cozy-weekend-afternoon-lifestyle-photo-.webp'),
      getFirebaseV2Url('a-candid-lifestyle-photo-of-a-young-asian-woman-si.webp'),
      getFirebaseV2Url('a-bright-and-fresh-morning-documentary-style-photo.webp'),
      getFirebaseV2Url('a-candid-workplace-photo-in-a-modern-office-corner.webp'),
      getFirebaseV2Url('ugc-style-phone-photo--a-teenage-chinese-singapore.webp'),
      getFirebaseV2Url('a-minimalist-yoga-studio-scene--a-woman-who-just-f.webp'),
      getFirebaseV2Url('ugc-style-phone-photo--a-middle-aged-chinese-singa.webp'),
      getFirebaseV2Url('ugc-style-phone-photo--a-middle-aged-malay-singapo.webp'),
      getFirebaseV2Url('ugc-style-phone-photo--a-young-chinese-singaporean.webp'),
      getFirebaseV2Url('ugc-style-phone-photo--a-young-indian-singaporean- (1).webp'),
      getFirebaseV2Url('ugc-style-phone-photo--a-young-indian-singaporean-.webp'),
      getFirebaseV2Url('ugc-style-phone-photo--a-young-malay-singaporean-m.webp'),
      getFirebaseV2Url('ugc-style-phone-photo--a-young-singaporean-woman--.webp'),
      getFirebaseV2Url('ugc-style-phone-photo--an-elderly-chinese-singapor.webp'),
      getFirebaseV2Url('ugc-style-phone-photo--an-older-malay-singaporean-.webp'),
    ],
  },
  audience: {
    workplace: [
      getFirebaseUrl('Facebook上班族.jpg')
    ],
    maternity: [
      getFirebaseUrl('产后妈妈场景_正确包装.jpg'),
      getFirebaseUrl('产后妈妈的温柔呵护.png'),
      getFirebaseUrl('产后妈妈坐月子喝滴鸡精.jpg')
    ],
    recovery: [
      getFirebaseUrl('银发族家庭场景_正确包装.jpg'),
      getFirebaseUrl('陪伴父母的爱.jpg'),
      getFirebaseUrl('子女陪术后父母喝滴鸡精.png')
    ],
    halal: [
      getFirebaseUrl('Halal屠宰与加工_1.png'),
      getFirebaseUrl('Halal屠宰与加工_2.png'),
      getFirebaseUrl('Halal屠宰与加工_3.png')
    ]
  },
  problems: {
    urbanProfessional: getFirebaseUrl('Facebook上班族.jpg'),
    motherCare: getFirebaseUrl('产后妈妈场景_正确包装.jpg')
  }
};
