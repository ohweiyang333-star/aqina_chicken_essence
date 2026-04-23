export function getFirebaseUrl(filename: string) {
  return `https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/${encodeURIComponent(filename)}?alt=media`;
}

export function getFirebaseV2Url(filename: string) {
  return getFirebaseUrl(`V2/${filename}`);
}

export const IMAGE_VERSION = '20260423d';

export function withImageVersion(path: string) {
  if (!path.startsWith('/')) {
    return path;
  }
  if (path.includes('v=')) {
    return path;
  }
  if (path.includes('?')) {
    return `${path}&v=${IMAGE_VERSION}`;
  }
  return `${path}?v=${IMAGE_VERSION}`;
}

export const IMAGES = {
  hero: withImageVersion('/images/hero-farm-banner.jpg'),
  logo: getFirebaseV2Url('Aqina Farm-Logo (Gold).webp'),
  story: getFirebaseUrl('7天双重蒸煮.jpg'),
  trust: {
    complianceBadge: getFirebaseV2Url('HACCP GMP ISO 认证 Logo.png'),
  },
  products: {
    box1: withImageVersion('/images/pack-1.webp'),
    box2: withImageVersion('/images/pack-2.webp'),
    box4: withImageVersion('/images/pack-4.webp'),
    box6: withImageVersion('/images/pack-6.webp'),
    boxMain: withImageVersion('/images/pack-1.webp'),
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
