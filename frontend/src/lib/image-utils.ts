export function getFirebaseUrl(filename: string) {
  return `https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/${encodeURIComponent(filename)}?alt=media`;
}

export const IMAGES = {
  hero: getFirebaseUrl('温暖家庭场景Hero Banner.png'),
  logo: getFirebaseUrl('Aqina Farm-Logo (Gold).png'),
  story: getFirebaseUrl('7天双重蒸煮.jpg'),
  products: {
    box1: '/images/pack-1.webp',
    box2: '/images/pack-2.webp',
    box4: '/images/pack-4.webp',
    box6: '/images/pack-6.webp',
    boxMain: getFirebaseUrl('主图-纯白背景.png'),
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
