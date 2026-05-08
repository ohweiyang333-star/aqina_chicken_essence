'use client';

import { useState } from 'react';
import { X, CheckCircle, Loader2, MessageCircle, QrCode, UploadCloud } from 'lucide-react';
import { useLocale, useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import {
  CheckoutOrderError,
  createOrder,
  type CheckoutOrderErrorCode,
} from '@/lib/order-service';
import { aqinaSiteConfig, getV2WhatsAppHref } from '@/lib/site-config';
import {
  createMarketingEventId,
  getMarketingServerEventContext,
  trackLandingFunnelEvent,
  trackReceiptSubmittedAsAddToCart,
} from '@/lib/marketing-analytics';

interface CheckoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  product: {
    name: string;
    price: number;
    id: string | number;
    label: string;
  } | null;
}

function resolvePackage(product: NonNullable<CheckoutModalProps['product']>) {
  const text = `${product.id} ${product.name} ${product.label}`.toLowerCase();
  if (text.includes('pack6') || text.includes('42') || text.includes('6盒') || text.includes('6 box')) {
    return { productId: 'pack6', boxCount: 6 };
  }
  if (text.includes('pack4') || text.includes('28') || text.includes('4盒') || text.includes('4 box')) {
    return { productId: 'pack4', boxCount: 4 };
  }
  if (text.includes('pack2') || text.includes('14') || text.includes('2盒') || text.includes('2 box')) {
    return { productId: 'pack2', boxCount: 2 };
  }
  return { productId: 'pack1', boxCount: 1 };
}

const checkoutTextInputClassName =
  'w-full rounded-xl border border-charcoal/10 bg-white px-5 py-4 text-charcoal caret-charcoal outline-none transition-all placeholder:text-charcoal/45 selection:bg-primary/25 focus:border-primary focus:ring-4 focus:ring-primary/10';
const ALLOWED_RECEIPT_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp']);
const MAX_RECEIPT_BYTES = 8 * 1024 * 1024;

function normalizePhone(value: string) {
  return value.replace(/\D/g, '');
}

export default function CheckoutModal({ isOpen, onClose, product }: CheckoutModalProps) {
  const ct = useTranslations('Index.Checkout');
  const locale = useLocale();
  const pathname = usePathname();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [orderId, setOrderId] = useState('');
  const [paymentReceipt, setPaymentReceipt] = useState<File | null>(null);
  const [formError, setFormError] = useState('');
  const [formData, setFormData] = useState({
    customerName: '',
    customerPhone: '',
    address: '',
  });

  if (!isOpen || !product) return null;

  const selectedPackage = resolvePackage(product);
  const shippingFee = selectedPackage.boxCount >= 2 ? 0 : 8;
  const subtotal = Number(product.price);
  const total = subtotal + shippingFee;
  const isV2Landing = pathname?.startsWith('/v2/');
  const v2CheckoutWhatsAppHref = getV2WhatsAppHref(locale, product.name);
  const rawPaymentSteps = ct.raw('payment.steps');
  const paymentSteps = Array.isArray(rawPaymentSteps)
    ? rawPaymentSteps.filter((step): step is string => typeof step === 'string')
    : [];

  const resetAndClose = () => {
    setIsSuccess(false);
    setOrderId('');
    setPaymentReceipt(null);
    setFormError('');
    setFormData({ customerName: '', customerPhone: '', address: '' });
    onClose();
  };

  const errorMessageForCode = (code: CheckoutOrderErrorCode) => {
    const messages: Record<CheckoutOrderErrorCode, string> = {
      nameRequired: ct('form.nameRequired') || 'Please enter your full name.',
      phoneInvalid:
        ct('form.phoneInvalid') || 'Enter a valid WhatsApp number with 8 to 20 digits.',
      addressInvalid:
        ct('form.addressInvalid') || 'Enter a Singapore delivery address with 10 to 500 characters.',
      receiptRequired:
        ct('form.receiptRequired') || 'Please upload your PayNow payment receipt before submitting.',
      receiptInvalidType:
        ct('form.receiptInvalidType') || 'Upload a JPG, PNG, or WebP receipt screenshot.',
      receiptTooLarge:
        ct('form.receiptTooLarge') || 'Upload a receipt screenshot smaller than 8MB.',
      unknownPackage:
        ct('form.unknownPackage') || 'This selected package is unavailable. Please choose a plan again.',
      submitError:
        ct('form.submitError') || 'Order submission failed. Please try again or contact via WhatsApp.',
    };

    return messages[code];
  };

  const validateReceiptFile = (file: File | null) => {
    if (!file) return errorMessageForCode('receiptRequired');
    if (!ALLOWED_RECEIPT_TYPES.has(file.type)) return errorMessageForCode('receiptInvalidType');
    if (file.size > MAX_RECEIPT_BYTES) return errorMessageForCode('receiptTooLarge');
    return '';
  };

  const resolveSubmissionError = (error: unknown) => {
    if (error instanceof CheckoutOrderError) {
      if (error.code === 'submitError' && error.message) return error.message;
      return errorMessageForCode(error.code);
    }

    return error instanceof Error && error.message
      ? error.message
      : errorMessageForCode('submitError');
  };

  const handleReceiptChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    const fileError = validateReceiptFile(file);
    if (fileError) {
      setPaymentReceipt(null);
      setFormError(fileError);
      event.target.value = '';
      return;
    }

    setPaymentReceipt(file);
    setFormError('');
    trackLandingFunnelEvent('receipt_upload_start', {
      source: 'checkout_modal',
      product_id: selectedPackage.productId,
      product_name: product.name,
      receipt_type: file?.type,
      receipt_size: file?.size,
    });
  };

  const handleCheckoutWhatsAppClick = () => {
    trackLandingFunnelEvent('checkout_whatsapp_fallback_click', {
      source: 'v2_checkout_whatsapp_fallback',
      destination: 'whatsapp',
      product_id: selectedPackage.productId,
      product_name: product.name,
      product_value: subtotal,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    const normalizedName = formData.customerName.trim();
    const normalizedPhone = normalizePhone(formData.customerPhone);
    const normalizedAddress = formData.address.trim();

    if (!normalizedName) {
      setFormError(errorMessageForCode('nameRequired'));
      return;
    }
    if (normalizedPhone.length < 8 || normalizedPhone.length > 20) {
      setFormError(errorMessageForCode('phoneInvalid'));
      return;
    }
    if (normalizedAddress.length < 10 || normalizedAddress.length > 500) {
      setFormError(errorMessageForCode('addressInvalid'));
      return;
    }

    const receiptFile = paymentReceipt;
    const fileError = validateReceiptFile(receiptFile);
    if (fileError) {
      setFormError(fileError);
      return;
    }
    if (!receiptFile) return;

    setIsSubmitting(true);
    const marketingEventId = createMarketingEventId('receipt_add_to_cart');
    const marketing = getMarketingServerEventContext(marketingEventId);

    try {
      const result = await createOrder({
        customerName: normalizedName,
        customerPhone: normalizedPhone,
        address: normalizedAddress,
        productId: selectedPackage.productId,
        receiptFile,
        marketing,
      });
      setOrderId(result || '');
      trackReceiptSubmittedAsAddToCart({
        productId: selectedPackage.productId,
        productName: product.name,
        value: total,
        packageLabel: product.label,
        orderId: result || undefined,
        eventId: marketingEventId,
      });
      trackLandingFunnelEvent('checkout_submit_success', {
        source: 'checkout_modal',
        product_id: selectedPackage.productId,
        product_name: product.name,
        order_id: result || undefined,
        value: total,
        currency: 'SGD',
      });
      setIsSuccess(true);
    } catch (error) {
      const submissionError = resolveSubmissionError(error);
      trackLandingFunnelEvent('checkout_submit_error', {
        source: 'checkout_modal',
        product_id: selectedPackage.productId,
        product_name: product.name,
        error_message: submissionError,
      });
      setFormError(submissionError);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="fixed inset-0 z-[300] flex items-center justify-center p-6 bg-charcoal/60 backdrop-blur-md">
        <div className="bg-white rounded-3xl p-10 max-w-lg w-full shadow-2xl text-center space-y-6 overflow-y-auto max-h-[90vh]">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto text-green-600">
            <CheckCircle size={40} />
          </div>

          <h2 className="text-3xl font-bold text-charcoal">
            {ct('success.title') || 'Order Received!'}
          </h2>

          <p className="text-charcoal/60">
            {ct('success.subtitle') || 'Thank you. Your order and PayNow receipt have been submitted for confirmation.'}
          </p>

          {/* Order ID */}
          {orderId && (
            <div className="p-4 bg-ivory rounded-xl border border-charcoal/10">
              <p className="text-xs text-charcoal/40 uppercase tracking-widest mb-1">
                {ct('success.orderIdLabel') || 'Order ID'}
              </p>
              <p className="font-mono font-bold text-charcoal">{orderId}</p>
            </div>
          )}

          <div className="text-left space-y-4 pt-4 border-t border-charcoal/10">
            <div className="p-4 bg-green-50 rounded-xl border border-green-100">
              <p className="text-sm leading-6 text-green-800">
                {ct('success.receiptSubmitted') || 'We have received your PayNow receipt. The team will verify payment manually before arranging delivery.'}
              </p>
            </div>
          </div>

          <button
            onClick={resetAndClose}
            className="w-full py-4 rounded-xl bg-charcoal text-ivory font-bold hover:bg-primary transition-all"
          >
            {ct('success.close') || 'Back to Home'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-[300] flex items-center justify-center p-6 bg-charcoal/60 backdrop-blur-md">
      <div className="bg-white rounded-3xl overflow-hidden max-w-xl w-full shadow-2xl flex flex-col max-h-[90vh]">
        <div className="p-6 border-b border-charcoal/5 flex justify-between items-center bg-ivory/50">
          <div>
            <h2 className="text-xl font-bold text-charcoal">
              {ct('form.title') || 'Complete Your Order'}
            </h2>
            <p className="text-sm text-charcoal/60">
              {product.name} — SGD {total.toFixed(2)}
            </p>
          </div>
          <button onClick={resetAndClose} className="p-2 hover:bg-charcoal/10 rounded-full transition-colors text-charcoal/40">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-8 space-y-6 overflow-y-auto">
          {formError && (
            <div
              id="checkout-form-error"
              role="alert"
              className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-800"
            >
              <p className="font-bold">{ct('form.errorTitle') || 'Please check your order details'}</p>
              <p>{formError}</p>
            </div>
          )}

          <div className="space-y-4 rounded-2xl border border-secondary/12 bg-secondary/5 p-5">
            <div className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-start">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-charcoal/40">
                  {ct('form.selectedPlan') || 'Selected plan'}
                </p>
                <p className="mt-1 text-lg font-black text-charcoal">{product.name}</p>
                <p className="text-sm text-charcoal/55">{product.label}</p>
              </div>
              <div className="rounded-xl bg-white px-4 py-3 sm:min-w-40 sm:text-right">
                <p className="text-xs font-bold uppercase tracking-widest text-charcoal/40">
                  {ct('form.total') || 'Total'}
                </p>
                <p className="mt-1 text-xl font-black text-charcoal">SGD {total.toFixed(2)}</p>
                <p className={shippingFee === 0 ? 'text-xs font-bold text-green-600' : 'text-xs text-charcoal/50'}>
                  {shippingFee === 0
                    ? (ct('form.free') || 'FREE')
                    : `${ct('form.delivery') || 'Delivery Fee'} SGD ${shippingFee.toFixed(2)}`}
                </p>
              </div>
            </div>

            {paymentSteps.length > 0 && (
              <ol className="grid gap-2 rounded-2xl border border-charcoal/10 bg-white p-4 text-sm font-semibold leading-6 text-charcoal/70 sm:grid-cols-3">
                {paymentSteps.map((step, index) => (
                  <li key={step} className="flex gap-2">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-charcoal text-xs font-black text-ivory">
                      {index + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            )}

            {isV2Landing && (
              <div className="rounded-2xl border border-green-200 bg-green-50 p-4 sm:flex sm:items-center sm:justify-between sm:gap-4">
                <div>
                  <p className="text-sm font-black text-green-900">
                    {ct('support.title') || 'Need help before paying?'}
                  </p>
                  <p className="mt-1 text-sm leading-6 text-green-800/80">
                    {ct('support.body') || 'Ask us on WhatsApp if you are unsure about this plan.'}
                  </p>
                </div>
                <a
                  id="v2-checkout-whatsapp-fallback"
                  href={v2CheckoutWhatsAppHref}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={handleCheckoutWhatsAppClick}
                  className="mt-3 inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-[#25D366] px-4 text-sm font-bold text-white shadow-[0_10px_24px_rgba(37,211,102,0.24)] transition hover:-translate-y-0.5 sm:mt-0"
                >
                  <MessageCircle size={17} />
                  <span>{ct('support.cta') || 'Ask about this plan'}</span>
                </a>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="checkout-customer-name" className="text-xs font-bold text-charcoal/40 uppercase tracking-widest pl-1">
              {ct('form.name') || 'Full Name'}
            </label>
            <input
              id="checkout-customer-name"
              required
              type="text"
              placeholder={ct('form.namePlaceholder') || 'Your full name'}
              className={checkoutTextInputClassName}
              value={formData.customerName}
              aria-describedby={formError ? 'checkout-form-error' : undefined}
              onChange={(e) => {
                setFormError('');
                setFormData({ ...formData, customerName: e.target.value });
              }}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="checkout-customer-phone" className="text-xs font-bold text-charcoal/40 uppercase tracking-widest pl-1">
              {ct('form.phone') || 'WhatsApp Phone'}
            </label>
            <input
              id="checkout-customer-phone"
              required
              type="tel"
              inputMode="tel"
              placeholder="+65 ..."
              className={checkoutTextInputClassName}
              value={formData.customerPhone}
              aria-describedby={formError ? 'checkout-form-error' : undefined}
              onChange={(e) => {
                setFormError('');
                setFormData({ ...formData, customerPhone: e.target.value });
              }}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="checkout-delivery-address" className="text-xs font-bold text-charcoal/40 uppercase tracking-widest pl-1">
              {ct('form.address') || 'Delivery Address'}
            </label>
            <textarea
              id="checkout-delivery-address"
              required
              rows={3}
              placeholder={ct('form.addressPlaceholder') || 'Singapore delivery address'}
              className={`${checkoutTextInputClassName} resize-none`}
              value={formData.address}
              aria-describedby={formError ? 'checkout-form-error' : undefined}
              onChange={(e) => {
                setFormError('');
                setFormData({ ...formData, address: e.target.value });
              }}
            />
          </div>

          <div className="rounded-2xl border border-charcoal/10 bg-ivory/60 p-5">
            <div className="grid gap-5 sm:grid-cols-[12rem_1fr]">
              <div className="flex justify-center">
                {aqinaSiteConfig.commerce.paymentQrImage ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={aqinaSiteConfig.commerce.paymentQrImage}
                    alt={aqinaSiteConfig.commerce.paymentQrAlt}
                    className="h-48 w-48 rounded-xl border border-charcoal/10 object-cover shadow-sm"
                  />
                ) : (
                  <div className="flex h-48 w-48 flex-col items-center justify-center rounded-xl border border-dashed border-charcoal/20 bg-charcoal/5 px-5 text-center">
                    <QrCode size={34} className="text-charcoal/30" />
                    <p className="mt-3 text-xs leading-5 text-charcoal/50">
                      {ct('payment.qrUnavailable') || 'PayNow QR details will be shared by WhatsApp.'}
                    </p>
                  </div>
                )}
              </div>
              <div className="space-y-3 text-sm leading-6 text-charcoal/70">
                <p className="text-base font-black text-charcoal">{ct('payment.paynow') || 'PayNow'}</p>
                <p>
                  <span className="font-bold text-charcoal">{ct('payment.accountName') || 'Account'}:</span>{' '}
                  {aqinaSiteConfig.commerce.paymentAccountName}
                </p>
                <p>
                  <span className="font-bold text-charcoal">{ct('payment.amount') || 'Amount'}:</span>{' '}
                  SGD {total.toFixed(2)}
                </p>
                <p>{ct('payment.beforeSubmit') || 'Please complete PayNow payment first, then upload the successful payment screenshot below to submit your order.'}</p>
                <p className="text-xs text-charcoal/45">
                  {ct('payment.referenceBeforeOrder') || 'Reference: your WhatsApp number'}
                </p>
              </div>
            </div>
          </div>

          <label className="block rounded-2xl border border-dashed border-charcoal/20 bg-white p-5">
            <span className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-charcoal/40">
              <UploadCloud size={16} />
              {ct('form.receipt') || 'PayNow Receipt Screenshot'}
            </span>
            <input
              id="checkout-payment-receipt"
              required
              type="file"
              accept="image/png,image/jpeg,image/webp"
              className="block w-full text-sm text-charcoal/70 file:mr-4 file:rounded-lg file:border-0 file:bg-charcoal file:px-4 file:py-2 file:text-sm file:font-bold file:text-ivory"
              aria-describedby={formError ? 'checkout-form-error' : undefined}
              onChange={handleReceiptChange}
            />
            <span className="mt-3 block text-xs leading-5 text-charcoal/45">
              {paymentReceipt
                ? paymentReceipt.name
                : ct('form.receiptHelp') || 'Upload JPG, PNG, or WebP after successful PayNow payment.'}
            </span>
          </label>

          <button
            id="checkout-submit-order"
            type="submit"
            disabled={isSubmitting || !paymentReceipt}
            className="w-full py-5 rounded-xl bg-charcoal text-ivory font-bold hover:bg-primary disabled:opacity-50 disabled:cursor-wait transition-all flex items-center justify-center space-x-3 shadow-xl shadow-charcoal/20"
          >
            {isSubmitting ? (
              <Loader2 className="animate-spin" />
            ) : (
              <span>{ct('form.submit') || 'Confirm Order'}</span>
            )}
          </button>

          <p className="text-[10px] text-center text-charcoal/30 leading-relaxed">
            {ct('form.terms') || 'By clicking confirm, your order is submitted. Payment will be handled via PayNow. Returns accepted within 7 days for quality issues.'}
          </p>
        </form>
      </div>
    </div>
  );
}
