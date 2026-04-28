import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { QrCode, ReceiptText, ShieldCheck, Sparkles } from "lucide-react";

import { getMarketingCheckout } from "@/lib/backend-marketing-service";
import { aqinaSiteConfig, getWhatsAppHref } from "@/lib/site-config";

export const metadata: Metadata = {
  title: "Aqina PayNow Checkout",
  description: "Complete your Aqina order securely with PayNow in Singapore.",
};

type PageProps = {
  params: Promise<{ token: string }>;
  searchParams?: Promise<{ lang?: string }>;
};

type PayNowLocale = "en" | "zh";

type PayNowCopy = {
  languageSwitch: string;
  pageTitle: string;
  intro: string;
  orderIdLabel: string;
  orderSummaryTitle: string;
  orderSummaryDescription: string;
  customerName: string;
  paymentMethod: string;
  orderStatus: string;
  deliveryAddress: string;
  total: string;
  scanTitle: string;
  scanDescription: string;
  qrMissing: string;
  accountName: string;
  referenceLabel: string;
  paymentNote: string;
  supportWhatsApp: string;
  sendProof: string;
  manualNote: string;
  whatsappMessage: (orderId: string) => string;
};

const payNowCopy: Record<PayNowLocale, PayNowCopy> = {
  en: {
    languageSwitch: "中文",
    pageTitle: "PayNow Checkout",
    intro:
      "Your chat order has been created. Please complete payment with PayNow and send the payment screenshot to our WhatsApp support so we can arrange delivery quickly.",
    orderIdLabel: "Order ID",
    orderSummaryTitle: "Order Summary",
    orderSummaryDescription: "Aqina will arrange Singapore delivery using the details below.",
    customerName: "Recipient",
    paymentMethod: "Payment Method",
    orderStatus: "Order Status",
    deliveryAddress: "Delivery Address",
    total: "Total",
    scanTitle: "Scan PayNow",
    scanDescription: "Please use Singapore PayNow to complete your payment.",
    qrMissing: "PayNow QR has not been configured yet. Please contact Aqina support for payment details.",
    accountName: "PayNow Account",
    referenceLabel: "Reference",
    paymentNote: "Payment Note",
    supportWhatsApp: "Support WhatsApp",
    sendProof: "I have paid. Send screenshot to WhatsApp",
    manualNote:
      "Payment verification is handled manually. After scanning PayNow, send your payment screenshot to our WhatsApp support and we will follow up as soon as possible.",
    whatsappMessage: (orderId: string) => `Hi Aqina SG, I have completed PayNow payment for ${orderId}.`,
  },
  zh: {
    languageSwitch: "EN",
    pageTitle: "PayNow 付款",
    intro:
      "您的聊天订单已经生成。请使用 PayNow 完成付款，并把付款截图发回公用 WhatsApp，我们会尽快为您安排发货。",
    orderIdLabel: "订单号",
    orderSummaryTitle: "订单摘要",
    orderSummaryDescription: "Aqina 会按照以下资料安排新加坡配送。",
    customerName: "收件人",
    paymentMethod: "付款方式",
    orderStatus: "订单状态",
    deliveryAddress: "收货地址",
    total: "总计",
    scanTitle: "扫描 PayNow",
    scanDescription: "请使用新加坡 PayNow 完成付款。",
    qrMissing: "尚未配置 PayNow QR 图片，请联系 Aqina 客服获取付款资料。",
    accountName: "PayNow 户名",
    referenceLabel: "付款备注",
    paymentNote: "付款备注",
    supportWhatsApp: "客服 WhatsApp",
    sendProof: "已付款，发送截图到公用 WhatsApp",
    manualNote:
      "当前支付完成后的核销仍由人工确认。你只需要扫码付款，再把截图发回公用 WhatsApp，我们就会尽快跟进。",
    whatsappMessage: (orderId: string) => `Hi Aqina SG，我已经完成订单 ${orderId} 的 PayNow 付款。`,
  },
};

export default async function PayNowCheckoutPage({ params, searchParams }: PageProps) {
  const { token } = await params;
  const resolvedSearchParams = await searchParams;
  const locale: PayNowLocale = resolvedSearchParams?.lang === "zh" ? "zh" : "en";
  const copy = payNowCopy[locale];
  const nextLocale: PayNowLocale = locale === "en" ? "zh" : "en";

  let checkout;
  try {
    checkout = await getMarketingCheckout(token);
  } catch {
    notFound();
  }

  const whatsappMessage = copy.whatsappMessage(checkout.order_id);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(189,139,78,0.2),_transparent_30%),linear-gradient(180deg,_#f8f4ee_0%,_#efe7d8_100%)] px-6 py-10 text-[#2b2018]">
      <section className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.08fr_0.92fr]">
        <div className="rounded-[32px] border border-white/70 bg-white/75 p-8 shadow-[0_26px_70px_rgba(75,48,24,0.1)] backdrop-blur">
          <div className="mb-8 flex items-start justify-between gap-6">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <div className="inline-flex items-center gap-2 rounded-full border border-[#ddc2a2] bg-[#fff8ee] px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-[#8e5d34]">
                  <Sparkles size={14} />
                  Aqina Singapore
                </div>
                <a
                  id="paynow-language-switch"
                  href={`/paynow/${token}?lang=${nextLocale}`}
                  className="inline-flex min-h-9 items-center rounded-full border border-[#ddc2a2] bg-white/70 px-4 text-xs font-bold uppercase tracking-[0.16em] text-[#6c4325] transition hover:bg-[#fff8ee]"
                >
                  {copy.languageSwitch}
                </a>
              </div>
              <h1 className="mt-4 text-4xl font-black tracking-tight">{copy.pageTitle}</h1>
              <p className="mt-2 max-w-xl text-sm leading-6 text-[#6c5849]">
                {copy.intro}
              </p>
            </div>

            <div className="rounded-[24px] bg-[#2b2018] px-5 py-4 text-right text-[#f7f2ea] shadow-lg">
              <p className="text-xs uppercase tracking-[0.24em] text-[#ceb89f]">{copy.orderIdLabel}</p>
              <p id="paynow-order-id" className="mt-2 font-mono text-sm font-bold">
                {checkout.order_id}
              </p>
            </div>
          </div>

          <div id="paynow-order-summary" className="rounded-[28px] border border-[#e7d8c7] bg-[#fffaf4] p-6">
            <div className="mb-5 flex items-center gap-3">
              <div className="rounded-2xl bg-[#2b2018] p-3 text-[#f7f2ea]">
                <ReceiptText size={18} />
              </div>
              <div>
                <h2 className="text-xl font-bold">{copy.orderSummaryTitle}</h2>
                <p className="text-sm text-[#6c5849]">{copy.orderSummaryDescription}</p>
              </div>
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              <InfoPair label={copy.customerName} value={checkout.customer_name} />
              <InfoPair label="WhatsApp" value={checkout.customer_whatsapp} />
              <InfoPair label={copy.paymentMethod} value="PayNow" />
              <InfoPair label={copy.orderStatus} value={checkout.order_status} />
            </div>

            <div className="mt-5 rounded-2xl bg-white p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#9b7954]">{copy.deliveryAddress}</p>
              <p className="mt-2 text-sm leading-6 text-[#3b2c21]">{checkout.delivery_address}</p>
            </div>

            <div className="mt-5 space-y-3">
              {checkout.items.map((item) => (
                <div
                  key={`${item.product_id}-${item.quantity}`}
                  className="flex items-center justify-between rounded-2xl border border-[#e7d8c7] bg-white px-4 py-4"
                >
                  <div>
                    <p className="font-semibold">
                      {locale === "zh"
                        ? item.product_name_zh || item.product_name
                        : item.product_name || item.product_name_zh}
                    </p>
                    <p className="text-sm text-[#6c5849]">x{item.quantity}</p>
                  </div>
                  <p className="text-lg font-black tracking-tight">SGD {item.total_price.toFixed(2)}</p>
                </div>
              ))}
            </div>

            <div className="mt-5 flex items-center justify-between rounded-2xl bg-[#2b2018] px-5 py-4 text-[#f7f2ea]">
              <span className="text-sm uppercase tracking-[0.22em] text-[#ceb89f]">{copy.total}</span>
              <span className="text-2xl font-black tracking-tight">SGD {checkout.total_amount.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="rounded-[32px] border border-white/70 bg-[#2b2018] p-8 text-[#f7f2ea] shadow-[0_26px_70px_rgba(75,48,24,0.12)]">
          <div className="mb-6 flex items-center gap-3">
            <div className="rounded-2xl bg-[#f7f2ea] p-3 text-[#2b2018]">
              <QrCode size={18} />
            </div>
            <div>
              <h2 className="text-2xl font-black tracking-tight">{copy.scanTitle}</h2>
              <p className="text-sm text-[#d8c8b3]">{copy.scanDescription}</p>
            </div>
          </div>

          <div
            id="paynow-qr-panel"
            className="rounded-[28px] border border-white/10 bg-white/5 p-6 text-center"
          >
            {checkout.paynow.payment_qr_image ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={checkout.paynow.payment_qr_image}
                alt={checkout.paynow.payment_qr_alt}
                className="mx-auto h-72 w-72 rounded-[28px] border border-white/10 object-cover shadow-2xl"
              />
            ) : (
              <div className="mx-auto flex h-72 w-72 flex-col items-center justify-center rounded-[28px] border border-dashed border-white/20 bg-white/5 px-8">
                <QrCode size={54} className="text-white/45" />
                <p className="mt-4 text-sm leading-6 text-[#d8c8b3]">
                  {copy.qrMissing}
                </p>
              </div>
            )}
          </div>

          <div className="mt-6 space-y-4 rounded-[28px] border border-white/10 bg-white/5 p-5">
            <InfoPairDark label={copy.accountName} value={checkout.paynow.account_name} />
            <InfoPairDark label={copy.referenceLabel} value={`${checkout.paynow.payment_reference_prefix}-${checkout.order_id}`} />
            <InfoPairDark label={copy.paymentNote} value={checkout.paynow.payment_note} />
            <InfoPairDark label={copy.supportWhatsApp} value={aqinaSiteConfig.contact.whatsappDisplay} />
          </div>

          <a
            id="paynow-whatsapp-proof"
            href={getWhatsAppHref(whatsappMessage)}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-6 flex w-full items-center justify-center rounded-full bg-[#f7f2ea] px-5 py-4 text-sm font-bold text-[#2b2018] transition hover:bg-[#fff8ee]"
          >
            {copy.sendProof}
          </a>

          <div className="mt-6 rounded-[24px] border border-[#735640] bg-[#3a2b21] p-5">
            <div className="flex items-start gap-3">
              <ShieldCheck size={18} className="mt-0.5 text-[#f1d5af]" />
              <p className="text-sm leading-6 text-[#e8d8c4]">
                {copy.manualNote}
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

function InfoPair({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#9b7954]">{label}</p>
      <p className="mt-2 text-sm font-semibold leading-6 text-[#3b2c21]">{value}</p>
    </div>
  );
}

function InfoPairDark({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#bfa58a]">{label}</p>
      <p className="mt-2 text-sm leading-6 text-[#f7f2ea]">{value}</p>
    </div>
  );
}
