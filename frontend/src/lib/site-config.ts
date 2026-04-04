const DEFAULT_WHATSAPP_DISPLAY = "+65 9000 0000";
const DEFAULT_WHATSAPP_LINK = "6590000000";
const DEFAULT_CONTACT_EMAIL = "sg-sales@aqina.com";
const DEFAULT_SHOPEE_URL = "https://shopee.sg/checkout";
const DEFAULT_WHATSAPP_MESSAGE =
  "Hi Aqina SG, I'm interested in your premium chicken essence.";

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
    shopeeUrl: readPublicEnv(
      process.env.NEXT_PUBLIC_SHOPEE_URL,
      DEFAULT_SHOPEE_URL,
    ),
    paymentQrImage: readPublicEnv(process.env.NEXT_PUBLIC_PAYMENT_QR_IMAGE),
    paymentQrAlt: readPublicEnv(
      process.env.NEXT_PUBLIC_PAYMENT_QR_ALT,
      "Aqina payment QR code",
    ),
  },
  messaging: {
    whatsappPrefill: readPublicEnv(
      process.env.NEXT_PUBLIC_WHATSAPP_PREFILL,
      DEFAULT_WHATSAPP_MESSAGE,
    ),
  },
};

export function getWhatsAppHref(
  message = aqinaSiteConfig.messaging.whatsappPrefill,
) {
  const encodedMessage = encodeURIComponent(message);
  return `https://wa.me/${aqinaSiteConfig.contact.whatsappLinkNumber}?text=${encodedMessage}`;
}
