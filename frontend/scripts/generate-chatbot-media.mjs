import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import sharp from "sharp";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendRoot = path.resolve(__dirname, "..");
const outDir = path.join(frontendRoot, "public", "chatbot");
const gptBrandIntroEnSource = path.join(frontendRoot, "scripts", "assets", "aqina-brand-intro-en-gpt-image-2.png");
const localBrandIntroSource = "/Users/ginooh/Documents/下载/create-a-high-impact-e-commerce-hero-product-image.jpg";
const remoteBrandIntroSource =
  "https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/create-a-high-impact-e-commerce-hero-product-image.jpg?alt=media&token=503ab227-91ad-41c9-a750-dadc9c3d86f0";

const posterSize = 1080;
const brand = {
  gold: "#b5812d",
  deepGold: "#7b4a13",
  green: "#1f6a3d",
  dark: "#2f2318",
  cream: "#fff6df",
  light: "#fffaf0",
};

const packagePosters = [
  {
    code: "pack1",
    source: "original-products/pack1.webp",
    zh: {
      eyebrow: "适合第一次尝试",
      title: "1盒体验装",
      subtitle: "7天入门滋养",
      chips: ["适合先试口感", "每日 1 包", "轻松开始"],
      badge: "1盒",
    },
    en: {
      eyebrow: "Perfect first step",
      title: "1-Box Starter Pack",
      subtitle: "7 Days of Nourishment",
      chips: ["Great for first-time trial", "1 pack daily", "Easy start"],
      badge: "1 BOX",
    },
  },
  {
    code: "pack2",
    source: "original-products/pack2.webp",
    zh: {
      eyebrow: "日常提神抗疲劳首选",
      title: "2盒14天疗程",
      subtitle: "满 SGD 70 包邮",
      chips: ["14 天补养节奏", "上班族推荐", "包邮更划算"],
      badge: "包邮",
    },
    en: {
      eyebrow: "Best for daily energy support",
      title: "2-Box 14-Day Pack",
      subtitle: "Free Delivery Included",
      chips: ["14-day routine", "Great for busy days", "Best starter value"],
      badge: "FREE DELIVERY",
    },
  },
  {
    code: "pack4",
    source: "original-products/pack4.webp",
    zh: {
      eyebrow: "孕产/月子补养推荐",
      title: "4盒28天调理",
      subtitle: "包邮",
      chips: ["孕产补养", "月子调理", "28 天更完整"],
      badge: "包邮",
    },
    en: {
      eyebrow: "Recommended for maternity care",
      title: "4-Box 28-Day Care Pack",
      subtitle: "Free delivery",
      chips: ["Maternity care", "Postpartum support", "28-day routine"],
      badge: "FREE DELIVERY",
    },
  },
  {
    code: "pack6",
    source: "original-products/pack6.webp",
    zh: {
      eyebrow: "长辈/送礼/家庭补养",
      title: "6盒42天家庭装",
      subtitle: "包邮更划算",
      chips: ["家庭长期补养", "送礼体面", "42 天储备"],
      badge: "更划算",
    },
    en: {
      eyebrow: "For elders, gifting & family care",
      title: "6-Box 42-Day Family Pack",
      subtitle: "Best long-term value",
      chips: ["Family nourishment", "Thoughtful gifting", "42-day supply"],
      badge: "BEST VALUE",
    },
  },
];

await fs.mkdir(outDir, { recursive: true });

await generateBrandIntroImages();
for (const poster of packagePosters) {
  await generatePackagePoster(poster, "zh", poster.zh);
  await generatePackagePoster(poster, "en", poster.en);
}

async function generateBrandIntroImages() {
  const sourceBuffer = await readBrandIntroSource();
  const zhPath = path.join(outDir, "aqina-brand-intro-zh.jpg");
  const enPath = path.join(outDir, "aqina-brand-intro-en.jpg");

  await sharp(sourceBuffer)
    .resize(posterSize, posterSize, { fit: "cover" })
    .jpeg({ quality: 90, mozjpeg: true })
    .toFile(zhPath);

  if (await fileExists(gptBrandIntroEnSource)) {
    await sharp(gptBrandIntroEnSource)
      .resize(posterSize, posterSize, { fit: "cover" })
      .jpeg({ quality: 90, mozjpeg: true })
      .toFile(enPath);
    return;
  }

  const overlay = svg(`
    <svg width="${posterSize}" height="${posterSize}" viewBox="0 0 ${posterSize} ${posterSize}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="10" stdDeviation="8" flood-color="#4a2e12" flood-opacity="0.28"/>
        </filter>
      </defs>
      <rect x="118" y="225" width="535" height="150" rx="54" fill="#fff1bf" fill-opacity="0.96" stroke="#fff8dc" stroke-width="5" filter="url(#shadow)"/>
      <text x="385" y="285" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="38" font-weight="800" fill="${brand.deepGold}">Raised on MD2</text>
      <text x="385" y="332" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="37" font-weight="800" fill="${brand.deepGold}">Golden Pineapples</text>
      <rect x="670" y="795" width="360" height="152" rx="32" fill="${brand.green}" fill-opacity="0.96" stroke="#efc772" stroke-width="5" filter="url(#shadow)"/>
      <text x="850" y="858" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="40" font-weight="900" fill="#fff8dd">100%</text>
      <text x="850" y="905" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="31" font-weight="800" fill="#fff8dd">Farm-to-Shelf</text>
      <text x="850" y="936" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="25" font-weight="700" fill="#fff8dd">Traceability</text>
    </svg>
  `);

  await sharp(sourceBuffer)
    .resize(posterSize, posterSize, { fit: "cover" })
    .composite([{ input: overlay, left: 0, top: 0 }])
    .jpeg({ quality: 90, mozjpeg: true })
    .toFile(enPath);
}

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function generatePackagePoster(poster, locale, copy) {
  const sourcePath = path.join(frontendRoot, "scripts", "assets", poster.source);
  const productBuffer = await sharp(sourcePath)
    .resize(520, 520, { fit: "contain", background: "#fff7e7" })
    .jpeg({ quality: 92, mozjpeg: true })
    .toBuffer();

  const productShadow = svg(`
    <svg width="720" height="720" viewBox="0 0 720 720" xmlns="http://www.w3.org/2000/svg">
      <ellipse cx="360" cy="630" rx="235" ry="42" fill="#6b451a" fill-opacity="0.22"/>
    </svg>
  `);

  const base = sharp({
    create: {
      width: posterSize,
      height: posterSize,
      channels: 3,
      background: brand.light,
    },
  });

  const background = svg(`
    <svg width="${posterSize}" height="${posterSize}" viewBox="0 0 ${posterSize} ${posterSize}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stop-color="#fff8e7"/>
          <stop offset="0.56" stop-color="#f8e5af"/>
          <stop offset="1" stop-color="#f5c85c"/>
        </linearGradient>
        <radialGradient id="glow" cx="78%" cy="22%" r="70%">
          <stop offset="0" stop-color="#ffffff" stop-opacity="0.86"/>
          <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
        </radialGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="10" stdDeviation="10" flood-color="#4a2e12" flood-opacity="0.22"/>
        </filter>
      </defs>
      <rect width="1080" height="1080" fill="url(#bg)"/>
      <rect width="1080" height="1080" fill="url(#glow)"/>
      <circle cx="940" cy="120" r="94" fill="#fff6d8" fill-opacity="0.45"/>
      <circle cx="94" cy="940" r="180" fill="#ffffff" fill-opacity="0.22"/>
      <rect x="54" y="54" width="972" height="972" rx="44" fill="none" stroke="#e3b85d" stroke-width="3" opacity="0.5"/>
      <text x="86" y="120" font-family="${fontFamily(locale)}" font-size="45" font-weight="800" fill="${brand.gold}" letter-spacing="3">AQINA</text>
      <text x="255" y="120" font-family="${fontFamily(locale)}" font-size="30" font-weight="500" fill="${brand.gold}">farm</text>
      <rect x="86" y="160" width="520" height="62" rx="31" fill="#fff8e5" fill-opacity="0.92" stroke="#ebca73" stroke-width="2"/>
      <text x="346" y="202" text-anchor="middle" font-family="${fontFamily(locale)}" font-size="${locale === "zh" ? 28 : 26}" font-weight="800" fill="${brand.deepGold}">${escapeXml(copy.eyebrow)}</text>
      <rect x="724" y="74" width="250" height="64" rx="32" fill="${brand.green}" filter="url(#shadow)"/>
      <text x="849" y="116" text-anchor="middle" font-family="${fontFamily(locale)}" font-size="${poster.code === "pack1" ? 28 : 23}" font-weight="900" fill="#fff9df">${escapeXml(copy.badge)}</text>
      <text x="88" y="306" font-family="${fontFamily(locale)}" font-size="${locale === "zh" ? 66 : titleSize(copy.title)}" font-weight="900" fill="${brand.dark}">${escapeXml(copy.title)}</text>
      <text x="92" y="372" font-family="${fontFamily(locale)}" font-size="${locale === "zh" ? 44 : subtitleSize(copy.subtitle)}" font-weight="800" fill="${brand.green}">${escapeXml(copy.subtitle)}</text>
      ${copy.chips.map((chip, index) => chipSvg(chip, locale, 88, 448 + index * 82)).join("")}
      <rect x="92" y="874" width="420" height="86" rx="30" fill="${brand.green}" filter="url(#shadow)"/>
      <text x="302" y="929" text-anchor="middle" font-family="${fontFamily(locale)}" font-size="${locale === "zh" ? 30 : 27}" font-weight="900" fill="#fff9df">${locale === "zh" ? "100% 纯鸡精" : "Pure Chicken Essence"}</text>
    </svg>
  `);

  await base
    .composite([
      { input: background, left: 0, top: 0 },
      { input: productShadow, left: 395, top: 350 },
      { input: productBuffer, left: 515, top: 405 },
    ])
    .jpeg({ quality: 91, mozjpeg: true })
    .toFile(path.join(outDir, `aqina-${poster.code}-chatbot-${locale}.jpg`));
}

async function readBrandIntroSource() {
  try {
    return await fs.readFile(localBrandIntroSource);
  } catch {
    const response = await fetch(remoteBrandIntroSource);
    if (!response.ok) {
      throw new Error(`Failed to fetch brand intro image: ${response.status}`);
    }
    return Buffer.from(await response.arrayBuffer());
  }
}

function chipSvg(text, locale, x, y) {
  return `
    <rect x="${x}" y="${y}" width="430" height="56" rx="28" fill="#fffdf4" fill-opacity="0.92" stroke="#e8bf61" stroke-width="2"/>
    <circle cx="${x + 31}" cy="${y + 28}" r="14" fill="${brand.gold}"/>
    <text x="${x + 58}" y="${y + 37}" font-family="${fontFamily(locale)}" font-size="${locale === "zh" ? 27 : 24}" font-weight="750" fill="${brand.dark}">${escapeXml(text)}</text>
  `;
}

function titleSize(title) {
  if (title.length > 24) return 40;
  if (title.length > 18) return 46;
  return 54;
}

function subtitleSize(subtitle) {
  if (subtitle.length > 25) return 31;
  if (subtitle.length > 18) return 35;
  return 39;
}

function fontFamily(locale) {
  return locale === "zh"
    ? "PingFang SC, Hiragino Sans GB, Noto Sans CJK SC, Arial, sans-serif"
    : "Inter, Arial, Helvetica, sans-serif";
}

function svg(markup) {
  return Buffer.from(markup);
}

function escapeXml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
