'use client';

import { useState } from 'react';
import { X, CheckCircle, Loader2, QrCode, UploadCloud } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { createOrder } from '@/lib/order-service';
import { aqinaSiteConfig } from '@/lib/site-config';

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

export default function CheckoutModal({ isOpen, onClose, product }: CheckoutModalProps) {
  const ct = useTranslations('Index.Checkout');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [orderId, setOrderId] = useState('');
  const [paymentReceipt, setPaymentReceipt] = useState<File | null>(null);
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

  const resetAndClose = () => {
    setIsSuccess(false);
    setOrderId('');
    setPaymentReceipt(null);
    setFormData({ customerName: '', customerPhone: '', address: '' });
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!paymentReceipt) {
      alert(ct('form.receiptRequired') || 'Please upload your PayNow payment receipt before submitting.');
      return;
    }
    setIsSubmitting(true);
    try {
      const result = await createOrder({
        customerName: formData.customerName,
        customerPhone: formData.customerPhone,
        address: formData.address,
        productId: selectedPackage.productId,
        receiptFile: paymentReceipt,
      });
      setOrderId(result || '');
      setIsSuccess(true);
    } catch {
      alert('Order submission failed. Please try again or contact via WhatsApp.');
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
              <p className="text-xs text-charcoal/40 uppercase tracking-widest mb-1">Order ID</p>
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
          <div className="space-y-2">
            <label className="text-xs font-bold text-charcoal/40 uppercase tracking-widest pl-1">
              {ct('form.name') || 'Name / 姓名'}
            </label>
            <input
              required
              type="text"
              placeholder="Your full name"
              className="w-full px-5 py-4 rounded-xl border border-charcoal/10 focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none transition-all"
              value={formData.customerName}
              onChange={(e) => setFormData({ ...formData, customerName: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-charcoal/40 uppercase tracking-widest pl-1">
              {ct('form.phone') || 'WhatsApp Phone / 电话'}
            </label>
            <input
              required
              type="tel"
              placeholder="+65 ..."
              className="w-full px-5 py-4 rounded-xl border border-charcoal/10 focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none transition-all"
              value={formData.customerPhone}
              onChange={(e) => setFormData({ ...formData, customerPhone: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-charcoal/40 uppercase tracking-widest pl-1">
              {ct('form.address') || 'Delivery Address / 地址'}
            </label>
            <textarea
              required
              rows={3}
              placeholder="Singapore Delivery Address"
              className="w-full px-5 py-4 rounded-xl border border-charcoal/10 focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none transition-all resize-none"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            />
          </div>

          <div className="p-6 bg-secondary/5 rounded-2xl border border-secondary/10 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-charcoal/60">{ct('form.subtotal') || 'Subtotal'}</span>
              <span className="font-bold text-charcoal">SGD {subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-charcoal/60">{ct('form.delivery') || 'Delivery Fee'}</span>
              <span className={shippingFee === 0 ? 'font-bold text-green-600' : 'font-bold text-charcoal'}>
                {shippingFee === 0 ? (ct('form.free') || 'FREE') : `SGD ${shippingFee.toFixed(2)}`}
              </span>
            </div>
            <div className="flex justify-between border-t border-secondary/15 pt-3 text-base">
              <span className="font-bold text-charcoal">{ct('form.total') || 'Total'}</span>
              <span className="font-black text-charcoal">SGD {total.toFixed(2)}</span>
            </div>
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
              required
              type="file"
              accept="image/png,image/jpeg,image/webp"
              className="block w-full text-sm text-charcoal/70 file:mr-4 file:rounded-lg file:border-0 file:bg-charcoal file:px-4 file:py-2 file:text-sm file:font-bold file:text-ivory"
              onChange={(event) => setPaymentReceipt(event.target.files?.[0] || null)}
            />
            <span className="mt-3 block text-xs leading-5 text-charcoal/45">
              {paymentReceipt
                ? paymentReceipt.name
                : ct('form.receiptHelp') || 'Upload JPG, PNG, or WebP after successful PayNow payment.'}
            </span>
          </label>

          <button
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
