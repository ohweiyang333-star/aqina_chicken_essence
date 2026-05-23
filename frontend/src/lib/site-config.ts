const DEFAULT_WHATSAPP_DISPLAY = "+65 9626 5734";
const DEFAULT_WHATSAPP_LINK = "6596265734";
const DEFAULT_CONTACT_EMAIL = "aqina_marketing@aqinafarm.com";
const DEFAULT_PAYNOW_QR_IMAGE =
  "https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/aqina-paynow-qr-designed.png?alt=media&token=c1c0596e-b35d-478b-b47a-31206ae3edfa";
const DEFAULT_PAYNOW_ACCOUNT_NAME = "Boong Poultry Pte Ltd";
const DEFAULT_WHATSAPP_MESSAGE =
  "Hi Aqina SG, I'm interested in your premium chicken essence.";
const DEFAULT_MESSENGER_LINK = "https://m.me/aqinafarmmy";

function readPublicEnv(value: string | undefined, fallback = "") {
  const trimmed = value?.trim();
  return trimmed ? trimmed : fallback;
}

function digitsOnly(value: string) {
  return value.replace(/\D/g, "");
}

const whatsappDisplay = readPublicEnv(
  process.env.NEXT_PUBLIC_WHATSAPP_DISPLAY,
  DEFAULT_WHATSAPP_DISPLAY,
);

const whatsappLinkNumber = digitsOnly(
  readPublicEnv(
    process.env.NEXT_PUBLIC_WHATSAPP_LINK,
    process.env.NEXT_PUBLIC_WHATSAPP_DISPLAY || DEFAULT_WHATSAPP_LINK,
  ),
);

export const aqinaSiteConfig = {
  contact: {
    whatsappDisplay,
    whatsappLinkNumber: whatsappLinkNumber || DEFAULT_WHATSAPP_LINK,
    email: readPublicEnv(
      process.env.NEXT_PUBLIC_CONTACT_EMAIL,
      DEFAULT_CONTACT_EMAIL,
    ),
  },
  commerce: {
    paymentQrImage: readPublicEnv(
      process.env.NEXT_PUBLIC_PAYMENT_QR_IMAGE,
      DEFAULT_PAYNOW_QR_IMAGE,
    ),
    paymentQrAlt: readPublicEnv(
      process.env.NEXT_PUBLIC_PAYMENT_QR_ALT,
      "Boong Poultry Pte Ltd PayNow QR",
    ),
    paymentAccountName: readPublicEnv(
      process.env.NEXT_PUBLIC_PAYMENT_ACCOUNT_NAME,
      DEFAULT_PAYNOW_ACCOUNT_NAME,
    ),
  },
  messaging: {
    whatsappPrefill: readPublicEnv(
      process.env.NEXT_PUBLIC_WHATSAPP_PREFILL,
      DEFAULT_WHATSAPP_MESSAGE,
    ),
    messengerHref: readPublicEnv(
      process.env.NEXT_PUBLIC_MESSENGER_LINK,
      DEFAULT_MESSENGER_LINK,
    ),
  },
};

export function getWhatsAppHref(
  message = aqinaSiteConfig.messaging.whatsappPrefill,
) {
  const encodedMessage = encodeURIComponent(message);
  return `https://wa.me/${aqinaSiteConfig.contact.whatsappLinkNumber}?text=${encodedMessage}`;
}

export function getV2WhatsAppPrefill(locale: string, productName?: string) {
  const isZh = locale === "zh";

  if (productName) {
    return isZh
      ? `Hi Aqina SG，我想问 ${productName} 是否适合我的日常饮用。`
      : `Hi Aqina SG, I would like to ask if ${productName} is suitable for my daily routine.`;
  }

  return isZh
    ? "Hi Aqina SG，我想确认自己适合 1盒试喝还是 2盒免运配套。"
    : "Hi Aqina SG, I want to confirm whether I should start with 1 box or the 2-box free delivery pack.";
}

export function getV2WhatsAppHref(locale: string, productName?: string) {
  return getWhatsAppHref(getV2WhatsAppPrefill(locale, productName));
}

export function getMessengerHref() {
  return aqinaSiteConfig.messaging.messengerHref;
}
