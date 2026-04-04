export function getFirebaseUrl(filename: string) {
  return `https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/${encodeURIComponent(filename)}?alt=media`;
}

export const IMAGES = {
  hero: getFirebaseUrl('温暖家庭场景Hero Banner.png'),
  logo: getFirebaseUrl('Aqina Farm-Logo (Gold).png'),
  story: getFirebaseUrl('7天双重蒸煮.jpg'),
  products: {
    box1: getFirebaseUrl('Aqina 一盒产品 - 客厅茶几.png'),
    box2: getFirebaseUrl('Aqina 两盒产品 - 餐厅桌.png'),
    box4: getFirebaseUrl('Aqina 四盒产品 - 厨房岛台（修正版）.png'),
    box6: getFirebaseUrl('Aqina 六盒产品 - 家居吧台.png'),
    boxMain: getFirebaseUrl('主图-纯白背景.png'),
  },
  audience: {
    workplace: [
      getFirebaseUrl('Facebook上班族.jpg'),
      getFirebaseUrl('小袋装特写.jpg'),
      getFirebaseUrl('滴鸡精液体倒入玻璃碗特写 - 真实包装.png')
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
