const FIREBASE_STORAGE_BUCKET = 'aqina-chicken-essence.firebasestorage.app';

export const STATIC_FIREBASE_IMAGE_TOKENS: Record<string, string> = {
  'V2/design-a-professional-website-hero-banner--use-the (1).webp':
    '19a027d8-a5ce-4fbe-a1d0-be287026e346',
  'V2/Aqina Farm-Logo (Gold).webp': '77f2a1e2-cde4-440e-9d0d-98c8ae6f1a3b',
  '7天双重蒸煮.jpg': 'a2164074-f5d5-4d27-8443-8fa4b3a16bf0',
  'V2/HACCP GMP ISO 认证 Logo.png': '344e99ae-ed12-4f2a-a33d-9cf0cd2e467b',
  'V2/Image 1.png': 'd7acf332-5139-4e9f-a317-3b088db104cc',
  'V2/Image 3.png': '2dfe2cd0-a130-41e5-9556-c25bdbd83aa2',
  'V2/clean-product-photography-for-a-landing-page--exac (3).webp':
    'c3d2d10d-80a5-4cf8-8cf0-f48cbd5cd567',
  'V2/clean-product-photography-for-a-landing-page--exac (2).webp':
    '9ebc16e0-a47b-48bf-8f21-e876612687bb',
  'V2/clean-product-photography-for-a-landing-page--exac.webp':
    '5b9bbf35-9a73-424f-93a8-a47061e481fa',
  'V2/clean-product-photography-for-a-landing-page--exac (1).webp':
    '088626b9-6409-406e-b7fe-ad466a02449a',
  'V2/a-warm-and-cozy-weekend-afternoon-lifestyle-photo-.webp':
    'ea4953f8-2f61-427e-a927-d7ffb380588b',
  'V2/a-candid-lifestyle-photo-of-a-young-asian-woman-si.webp':
    '8ce47638-5a99-44c1-a8d1-7d42423375b6',
  'V2/a-bright-and-fresh-morning-documentary-style-photo.webp':
    '3c222d0b-ce93-4015-9cdc-cb7b481b14cc',
  'V2/a-candid-workplace-photo-in-a-modern-office-corner.webp':
    '66defb1f-ee73-472a-8c21-b87c0d5b6124',
  'V2/ugc-style-phone-photo--a-teenage-chinese-singapore.webp':
    'f7e01cf8-4823-4fcf-a946-fa4ab820b938',
  'V2/a-minimalist-yoga-studio-scene--a-woman-who-just-f.webp':
    '29ac7b17-f095-49e7-9e41-339577bdc433',
  'V2/ugc-style-phone-photo--a-middle-aged-chinese-singa.webp':
    'b296adf2-447e-41da-8b2b-d9f1808963a5',
  'V2/ugc-style-phone-photo--a-middle-aged-malay-singapo.webp':
    '2ff3fc81-05e3-49f4-bc66-037899389ce1',
  'V2/ugc-style-phone-photo--a-young-chinese-singaporean.webp':
    '622f489d-6f66-453d-af8c-013a94cd1c9f',
  'V2/ugc-style-phone-photo--a-young-indian-singaporean- (1).webp':
    'fc376792-3baa-4c38-82db-12dcee722443',
  'V2/ugc-style-phone-photo--a-young-indian-singaporean-.webp':
    'ea8e8a57-68dd-42b7-9327-fa950cc702ce',
  'V2/ugc-style-phone-photo--a-young-malay-singaporean-m.webp':
    '734cb7eb-82bc-4286-a9fb-ee2a6bc04b55',
  'V2/ugc-style-phone-photo--a-young-singaporean-woman--.webp':
    'b288d38e-fc2c-423b-9c4c-bf57446385ec',
  'V2/ugc-style-phone-photo--an-elderly-chinese-singapor.webp':
    '612c2c47-4c08-428b-8287-fd61d06d1610',
  'V2/ugc-style-phone-photo--an-older-malay-singaporean-.webp':
    '4b6acf5b-3d4c-44c0-b269-1c6ff2144af0',
  'Facebook上班族.jpg': '73ad562b-e9c3-478b-927e-e963e262e1f2',
  '产后妈妈场景_正确包装.jpg': '4a54e16f-f4d3-4902-b866-7b9a149c9703',
  '产后妈妈的温柔呵护.png': '085d677b-6f2b-4230-a39b-171546e437e9',
  '产后妈妈坐月子喝滴鸡精.jpg': '54e0a028-747c-4cc9-98dd-0ef279585811',
  '银发族家庭场景_正确包装.jpg': '2a6b4a5d-ee2a-472c-b1e5-bb15c633c405',
  '陪伴父母的爱.jpg': 'fe772fa1-6309-4f09-bd6a-5a9524eccaa0',
  '子女陪术后父母喝滴鸡精.png': '895f6bcc-91ab-4cad-b0f1-d6f8d8198f01',
  'Halal屠宰与加工_1.png': 'b804e742-e95a-4071-9b61-8cfd3b23cdaa',
  'Halal屠宰与加工_2.png': '717481b4-bafd-4612-9947-983ec3c408eb',
  'Halal屠宰与加工_3.png': '05415dc9-64dd-4bb2-af69-2a1e420d28c7',
};

export function getFirebaseUrl(filename: string) {
  const token = STATIC_FIREBASE_IMAGE_TOKENS[filename];

  if (!token) {
    throw new Error(`Missing Firebase Storage download token for ${filename}`);
  }

  return `https://firebasestorage.googleapis.com/v0/b/${FIREBASE_STORAGE_BUCKET}/o/${encodeURIComponent(filename)}?alt=media&token=${encodeURIComponent(token)}`;
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
  hero: getFirebaseV2Url('design-a-professional-website-hero-banner--use-the (1).webp'),
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
