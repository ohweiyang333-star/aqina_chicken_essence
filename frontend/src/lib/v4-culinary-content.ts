export type V4Locale = "en" | "zh";
export type V4RecipeIcon = "clock" | "heart" | "flame";
export type V4SuperiorityIcon = "taste" | "purity" | "light";
export type V4PackKey = "pack1" | "pack2" | "pack4" | "pack6";

export const v4Media = {
  hero: "/v4/hero-golden-noodle-product.png",
  coldDinner: "/v4/frustration-cold-dinner.png",
  goldenDish: "/v4/fantasy-golden-dish-product.png",
  noodleSoup: "/v4/recipe-noodle-soup-product.png",
  steamedEgg: "/v4/recipe-steamed-egg-product.png",
  frogLegs: "/v4/recipe-frog-legs-product.png",
  finalTable: "/v4/final-family-table-product.png",
} as const;

export const v4GeneratedImageBrief = [
  "AI food scenes are generated with Aqina product packaging integrated into the photographed scene.",
  "The packaging reference is the official Aqina box and sachet appearance: white-gold carton, amber 7, AQINA farm mark, Chinese 纯鸡精, pineapple motif, and illustrated chicken.",
  "No web images are used. Ecommerce product cards still use the existing Firebase-backed IMAGES.products box1/box2/box4/box6 assets for exact pack display.",
  "Generated food scenes must avoid glass bottles, transparent bottles, generic supplement packaging, and pasted-on composition.",
];

export const v4CulinaryContent = {
  zh: {
    meta: {
      title: "Aqina 黄金原汤｜让滋补跟着美食一起入口",
      description:
        "Aqina MD2 菠萝酵素滴鸡精，把营养融入日常美食。零腥味、鲜甜回甘，面线、蒸蛋、家宴料理都能自由发挥，让健康过程也吃得丰盛。",
    },
    loadingLabel: "正在准备黄金原汤餐桌",
    hero: {
      eyebrow: "谁说滴鸡精只能捏着鼻子喝？",
      title: "健康补给，也可以跟着丰盛美食一起入口。",
      subtitle:
        "Aqina MD2 菠萝酵素滴鸡精。不加一滴水的双重炖煮，萃取出零腥味、鲜甜回甘的黄金精华。营养不必只靠硬喝，也能融进你喜欢的面、蛋、汤与家常菜里，随着热腾腾的美食进入身体。",
      cta: "询问套餐与下单协助",
      secondaryCta: "直接选择套餐",
      imageAlt: "热气腾腾的黄金海鲜面线汤",
      productAlt: "Aqina 黄金原汤产品包装",
      notes: ["零腥味回甘", "双重炖煮原汤", "快手菜与家宴都适合"],
    },
    frustration: {
      eyebrow: "下班后的厨房现实",
      title: "想补身体，也不一定要牺牲那一口好吃。",
      body:
        "很多人一想到滴鸡精，就想到单独喝、忍味道、像完成任务。但真正能坚持的健康方式，应该是你本来就想吃的一餐：快手宵夜、孩子的蒸蛋、周末家宴，都能顺手加一点营养。",
      turn: "现在，撕开包装，把黄金原汤加入你正在做的菜里，美味不被牺牲，营养也不被浪费。",
      coldLabel: "妥协的一餐",
      coldTitle: "外卖、泡面、淡而无味的晚餐",
      coldBody: "不是你不想好好吃饭，是下班后的身体真的没有力气再熬一锅汤。",
      warmLabel: "原汤一滴入魂",
      warmTitle: "热气腾腾、金灿灿、鲜甜回甘",
      warmBody: "黄金汤汁包裹食材，香气往上升，营养跟着一桌丰盛美食自然入口。",
      coldAlt: "冷色调的平淡下班晚餐",
      warmAlt: "暖色调的金黄原汤美食",
    },
    showcase: {
      eyebrow: "Culinary Showcase",
      title: "不用固定食谱，喜欢怎么吃就怎么发挥",
      subtitle:
        "下面只是灵感方向。你可以按家人口味自由搭配，把 Aqina 加进熟悉的料理里，让滋补变成更容易坚持的一餐。",
      recipes: [
        {
          id: "noodle",
          icon: "clock",
          label: "极致方便",
          title: "5分钟，把普通面线变成温暖补给",
          body:
            "累了一天不想大动干戈？煮好一份面线，起锅前撕开一包 Aqina 滴鸡精加入汤里。黄金凤梨鸡（Ayam Nanas）的鲜甜随着热气散开，汤汁裹着面条入口，营养也跟着这一碗热食进入身体。这不是固定食谱，只是最轻松的吃法之一。",
          image: v4Media.noodleSoup,
          imageAlt: "深夜灵魂面线汤",
          productNote: "起锅前倒入一包，面线立刻有老火汤底的厚度。",
        },
        {
          id: "egg",
          icon: "heart",
          label: "绝对健康",
          title: "把营养藏进家人本来就爱吃的蒸蛋",
          body:
            "可以用滴鸡精代替部分清水来打鸡蛋，蒸出来的水蛋更嫩滑，带着自然鲜甜。0 脂肪、0 添加，满满高纯度优质蛋白，让营养不再像任务，而是变成家人愿意多吃一口的日常料理。",
          image: v4Media.steamedEgg,
          imageAlt: "滴鸡精干贝蒸蛋",
          productNote: "用原汤取代清水，蒸蛋更滑、更鲜、更有底气。",
        },
        {
          id: "frog",
          icon: "flame",
          label: "纯粹美味",
          title: "周末家宴，也能吃得丰盛又有营养",
          body:
            "别把“滋补”想得太严肃。清蒸田鸡、鱼片、菇类、青菜或家里常做的热菜，都可以在出炉前趁热加入 Aqina 菠萝滴鸡精。金黄鸡汁渗进食材，鲜甜更完整，营养也随着丰盛的一餐被好好吃进去。众口难调，所以重点不是照抄食谱，而是按你家的口味自由发挥。",
          image: v4Media.frogLegs,
          imageAlt: "鸡精蒸田鸡",
          productNote: "出炉趁热淋上，金黄鸡汁直接渗进滑嫩肉质。",
        },
      ],
    },
    superiority: {
      eyebrow: "老饕的选择标准",
      title: "同样是入菜，为什么顶级老饕只选 Aqina？",
      items: [
        {
          icon: "taste",
          title: "拒绝腥苦，只留回甘。",
          body:
            "市面上许多鸡精加热后，容易泛起令人不悦的腥苦味，破坏整道菜的鲜度。而 Aqina 使用 MD2 菠萝酵素喂养的凤梨鸡，从源头减少腥味，留下更适合入菜的果香回甘与原汤鲜甜。",
        },
        {
          icon: "purity",
          title: "不稀释的鲜味炸弹。",
          body:
            "很多产品为了成本加水稀释。Aqina 采用双重炖煮蒸汽萃取，全程不加一滴水。它极高的纯度能瞬间唤醒食材的底味，提升整道菜的层次。",
        },
        {
          icon: "light",
          title: "清透如珀，绝不油腻。",
          body:
            "做菜最怕高汤厚重油腻。Aqina 经过精密过滤，0脂肪、0胆固醇。用它做底汤，汤色清透如珀，口感醇厚却丝毫不腻，全家老小吃得毫无负担。",
        },
      ],
    },
    offer: {
      eyebrow: "厨房升级套餐",
      title: "先选好套餐，今晚就能自由发挥。",
      subtitle:
        "从一周尝鲜到全家囤货，所有配套都能直接下单。想怎么煮不必被固定食谱限制，我们可以协助你选择适合人数和使用频率的套餐。",
      freeShipping: "免运费",
      mostPopular: "Most Popular",
      buyNow: "立即下单 - 开始我的黄金厨房",
      items: [
        {
          packKey: "pack1",
          title: "深夜食堂体验装",
          subtitle: "1盒7包 · SGD 39.90",
          body: "先试 7 包，把滴鸡精加入面、蛋、汤或你熟悉的热菜里。",
          badge: "尝鲜首选",
          features: ["7 包独立包装", "适合先试味道和入菜方式", "面线、蒸蛋、汤底、热菜都能自由发挥"],
        },
        {
          packKey: "pack2",
          title: "双周星厨常备装",
          subtitle: "2盒14包 · SGD 75.00",
          body: "两周份的黄金原汤，让快手早餐、下班晚餐和周末小家宴都有营养底气。",
          badge: "双周常备",
          features: ["覆盖 14 次入菜或直饮", "适合两人小家庭", "达到免运费门槛"],
        },
        {
          packKey: "pack4",
          title: "家庭星厨囤货装",
          subtitle: "4盒28包 · SGD 149.00",
          body:
            "覆盖全家的营养早餐、深夜热汤，以及周末按家人口味自由发挥的一桌好菜。",
          badge: "主推配套",
          features: ["28 包家庭常备", "早餐、宵夜、家宴都够用", "免运费，适合作为日常主力配套"],
        },
        {
          packKey: "pack6",
          title: "全家黄金厨房囤货装",
          subtitle: "6盒42包 · SGD 219.00",
          body: "适合多人家庭、长辈照顾、持续复购，把黄金原汤变成厨房里的日常底牌。",
          badge: "长期囤货",
          features: ["42 包长期库存", "适合全家共享与送礼", "减少断货，持续升级日常料理"],
        },
      ],
    },
    finalCta: {
      eyebrow: "把滋补变成好吃",
      title: "今晚开始，让营养跟着你爱吃的料理一起入口。",
      body:
        "不必等周末、不必熬 3 小时，也不必照着复杂食谱。撕开一包，加入热腾腾的料理里，健康过程也可以吃得丰盛。",
      productsCta: "选择我的黄金原汤套餐",
      whatsappCta: "WhatsApp 询问套餐 / 下单协助",
      whatsappMessage: "Hi Aqina SG，我想了解 Aqina 滴鸡精套餐、下单协助和简单烹饪灵感。",
      imageAlt: "Aqina 黄金原汤家庭厨房美食场景",
      productAlt: "Aqina 黄金原汤家庭囤货装",
    },
  },
  en: {
    meta: {
      title: "Aqina Golden Essence Stock | Nourishment Enjoyed Through Real Food",
      description:
        "Aqina MD2 pineapple enzyme chicken essence brings nourishment into everyday cooking. Clean, naturally sweet, and free from gamey heaviness, it lets healthy routines taste generous and satisfying.",
    },
    loadingLabel: "Preparing the golden stock table",
    hero: {
      eyebrow: "Who said chicken essence is only meant to be swallowed like medicine?",
      title: "Nourishment can enter the body with food you truly enjoy.",
      subtitle:
        "Aqina MD2 Pineapple Enzyme Chicken Essence is double-boiled without a single drop of added water, extracting a golden essence that is clean, sweet, and free from gamey heaviness. Instead of forcing nourishment as a chore, add it to noodles, eggs, soups, and family dishes so nutrition arrives with a generous meal.",
      cta: "Ask About Bundles / Order Help",
      secondaryCta: "Choose a Bundle",
      imageAlt: "Steaming golden seafood noodle soup",
      productAlt: "Aqina golden essence product packaging",
      notes: ["No gamey aftertaste", "Double-boiled pure stock", "For quick meals and family feasts"],
    },
    frustration: {
      eyebrow: "The kitchen reality after work",
      title: "Taking care of your health should not mean giving up good food.",
      body:
        "Many people think chicken essence means drinking it on its own and getting it over with. But the healthy routine that lasts is usually the one you already want to eat: a quick supper, a child's steamed egg, or a weekend family dish with one extra layer of nourishment.",
      turn:
        "Now, tear open one pack and add the golden essence to the food you are already cooking, so flavor stays enjoyable and nutrition is not wasted.",
      coldLabel: "The compromise meal",
      coldTitle: "Takeaway, instant noodles, and a flat dinner",
      coldBody:
        "It is not that you do not care. After a long workday, your body simply has no energy left to build a proper soup base.",
      warmLabel: "One golden drop of soul",
      warmTitle: "Steaming, glowing, sweet, and deeply savory",
      warmBody:
        "Golden essence wraps around the ingredients, aroma rises with the steam, and nourishment enters naturally with a generous meal.",
      coldAlt: "Cool-toned bland dinner after work",
      warmAlt: "Warm golden stock home cooking dish",
    },
    showcase: {
      eyebrow: "Culinary Showcase",
      title: "No fixed recipe needed. Cook it your way.",
      subtitle:
        "These are only inspiration starters. Add Aqina to familiar dishes and adjust freely to your family's taste, so nourishment becomes easier to keep up with.",
      recipes: [
        {
          id: "noodle",
          icon: "clock",
          label: "Ultimate Convenience",
          title: "Five minutes to turn simple noodles into warm nourishment",
          body:
            "Too tired to chop, prep, and cook from scratch? Boil a serving of mian xian, then tear open one pack of Aqina Chicken Essence right before serving. The natural sweetness of Ayam Nanas opens up in the steam, the golden broth coats every strand, and nourishment enters with a bowl you actually want to finish. This is only one easy idea, not a fixed recipe.",
          image: v4Media.noodleSoup,
          imageAlt: "Late-night golden mian xian noodle soup",
          productNote: "Pour one pack in before serving and the noodle soup gains the body of slow stock.",
        },
        {
          id: "egg",
          icon: "heart",
          label: "Clean Nutrition",
          title: "Fold nourishment into steamed egg your family already loves",
          body:
            "Use chicken essence to replace part of the water when beating eggs. The steamed egg turns softer and carries a natural sweetness. With 0 fat, 0 additives, and high-quality protein, nourishment no longer feels like a task. It becomes part of an everyday dish your family is happy to eat.",
          image: v4Media.steamedEgg,
          imageAlt: "Chicken essence scallop steamed egg",
          productNote: "Replace water with pure stock for steamed egg that is silkier, sweeter, and richer.",
        },
        {
          id: "frog",
          icon: "flame",
          label: "Pure Gourmet Pleasure",
          title: "Weekend family dishes can be generous and nourishing",
          body:
            "Do not make nourishment feel too serious. Steamed frog legs, fish slices, mushrooms, vegetables, or your family's usual hot dishes can all take Aqina Pineapple Chicken Essence before serving. The golden chicken essence sinks into the ingredients, rounds out the sweetness, and helps nutrition arrive through a full meal. Tastes differ, so the point is not to copy one recipe. Cook it your way.",
          image: v4Media.frogLegs,
          imageAlt: "Steamed frog legs with golden chicken essence sauce",
          productNote: "Pour while hot so the golden stock sinks straight into the tender meat.",
        },
      ],
    },
    superiority: {
      eyebrow: "The gourmet standard",
      title: "If every chicken essence can be cooked with, why do true food lovers choose Aqina?",
      items: [
        {
          icon: "taste",
          title: "No bitterness, no gamey finish, only clean sweetness.",
          body:
            "Many chicken essences turn gamey or bitter once heated, dulling the dish instead of lifting it. Aqina starts with MD2 pineapple-enzyme-fed Ayam Nanas, reducing unwanted heaviness from the source and leaving a clean fruity finish with real stock sweetness.",
        },
        {
          icon: "purity",
          title: "An undiluted flavor bomb.",
          body:
            "Many products are diluted with water for cost. Aqina is double-boiled and steam-extracted without adding a single drop of water. Its high purity wakes up the natural base flavor of ingredients and adds depth immediately.",
        },
        {
          icon: "light",
          title: "Amber-clear, never greasy.",
          body:
            "Heavy stock can make a dish oily and tiring. Aqina is carefully filtered with 0 fat and 0 cholesterol. The soup stays clear like amber, rich in taste yet light enough for the whole family.",
        },
      ],
    },
    offer: {
      eyebrow: "Kitchen Upgrade Bundles",
      title: "Choose a bundle first, then cook freely tonight.",
      subtitle:
        "From a one-week tasting box to family stock-up bundles, every option is ready to order. You do not need a strict recipe system. We can help you choose the right bundle for your household size and usage rhythm.",
      freeShipping: "Free shipping",
      mostPopular: "Most Popular",
      buyNow: "Order Now - Start My Golden Kitchen",
      items: [
        {
          packKey: "pack1",
          title: "Late-Night Kitchen Tasting Box",
          subtitle: "1 box, 7 packs · SGD 39.90",
          body: "Try seven packs in noodles, eggs, soups, or the warm dishes you already cook at home.",
          badge: "First Taste",
          features: ["7 individually packed servings", "Easy way to test flavor and cooking styles", "Works for noodles, steamed egg, soup base, and hot dishes"],
        },
        {
          packKey: "pack2",
          title: "Two-Week Home Chef Supply",
          subtitle: "2 boxes, 14 packs · SGD 75.00",
          body: "Two weeks of golden essence for fast breakfasts, after-work dinners, and small weekend dishes.",
          badge: "Two-Week Supply",
          features: ["14 cooking or drinking occasions", "Good for couples or small households", "Qualifies for free shipping"],
        },
        {
          packKey: "pack4",
          title: "Family Star-Chef Stock-Up",
          subtitle: "4 boxes, 28 packs · SGD 149.00",
          body:
            "Perfect for family breakfasts, late-night hot bowls, and weekend dishes adjusted to your family's taste.",
          badge: "Featured Bundle",
          features: ["28 packs for family use", "Breakfast, supper, and weekend meals", "Free shipping and strong as the everyday main bundle"],
        },
        {
          packKey: "pack6",
          title: "Full-Family Golden Kitchen Reserve",
          subtitle: "6 boxes, 42 packs · SGD 219.00",
          body:
            "For larger families, eldercare routines, and repeat buyers who want golden stock ready whenever the kitchen calls.",
          badge: "Long-Term Stock",
          features: ["42 packs for steady pantry supply", "Suitable for sharing and gifting", "Less risk of running out mid-routine"],
        },
      ],
    },
    finalCta: {
      eyebrow: "Make nourishment delicious",
      title: "Starting tonight, let nourishment enter with food you love.",
      body:
        "No need to wait for the weekend. No need to simmer for three hours. No need to follow a complicated recipe. Tear one pack open, add it to a hot dish, and make the healthy routine taste generous.",
      productsCta: "Choose My Golden Stock Bundle",
      whatsappCta: "WhatsApp Bundle / Order Help",
      whatsappMessage: "Hi Aqina SG, I want to know more about Aqina chicken essence bundles, order help, and simple cooking inspiration.",
      imageAlt: "Aqina golden stock home kitchen food scene",
      productAlt: "Aqina golden stock family bundle",
    },
  },
} as const;
