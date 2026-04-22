'use client';

import { useState } from 'react';
import { X, CheckCircle, Loader2, QrCode } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { createOrder } from '@/lib/order-service';
import { aqinaSiteConfig, getWhatsAppHref } from '@/lib/site-config';

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

export default function CheckoutModal({ isOpen, onClose, product }: CheckoutModalProps) {
  const ct = useTranslations('Index.Checkout');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [orderId, setOrderId] = useState('');
  const [formData, setFormData] = useState({
    customerName: '',
    customerPhone: '',
    address: '',
  });

  if (!isOpen || !product) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const result = await createOrder({
        customerName: formData.customerName,
        customerPhone: formData.customerPhone,
        address: formData.address,
        items: [{
          productId: String(product.id),
          productName: product.name,
          quantity: 1,
          price: product.price
        }],
        total: product.price
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
            {ct('success.subtitle') || 'Thank you for your order. Please complete payment using one of the methods below.'}
          </p>

          {/* Order ID */}
          {orderId && (
            <div className="p-4 bg-ivory rounded-xl border border-charcoal/10">
              <p className="text-xs text-charcoal/40 uppercase tracking-widest mb-1">Order ID</p>
              <p className="font-mono font-bold text-charcoal">{orderId}</p>
            </div>
          )}

          {/* Payment Instructions - Bilingual */}
          <div className="text-left space-y-4 pt-4 border-t border-charcoal/10">
            <h3 className="font-bold text-charcoal text-lg">
              {ct('payment.title') || 'Payment Instructions'}
            </h3>

            <div className="p-4 bg-ivory/50 rounded-xl space-y-2">
              <p className="text-sm text-charcoal leading-relaxed">
                {ct('payment.cn') || '下单后，请直接扫描下方 PayNow QR Code，并在参考栏填写您的订单号。支付成功后请截图发送至 WhatsApp 客服，我们会尽快为您安排发货。'}
              </p>
            </div>

            <div className="p-4 bg-ivory/50 rounded-xl space-y-2">
              <p className="text-sm text-charcoal leading-relaxed">
                {ct('payment.en') || 'After placing your order, please scan the PayNow QR code below and include your Order ID in the payment reference. Send your payment screenshot to our WhatsApp support so we can arrange delivery quickly.'}
              </p>
            </div>

            {/* PayNow QR Code */}
            <div className="space-y-3">
              <p className="text-sm font-semibold text-charcoal text-center">
                {ct('payment.paynow') || 'PayNow'}
              </p>
              <div className="flex justify-center">
                {aqinaSiteConfig.commerce.paymentQrImage ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={aqinaSiteConfig.commerce.paymentQrImage}
                    alt={aqinaSiteConfig.commerce.paymentQrAlt}
                    className="h-48 w-48 rounded-xl border border-charcoal/10 object-cover shadow-sm"
                  />
                ) : (
                  <div className="w-48 rounded-xl border border-dashed border-charcoal/20 bg-charcoal/5 px-5 py-6 text-center">
                    <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-white text-charcoal/30 shadow-sm">
                      <QrCode size={28} />
                    </div>
                    <p className="text-xs leading-5 text-charcoal/50">
                      {ct('payment.qrUnavailable') || 'PayNow QR details will be shared after order confirmation.'}
                    </p>
                  </div>
                )}
              </div>
              <p className="text-xs text-charcoal/40 text-center">
                {ct('payment.qrNote') || 'Reference: Your Order ID'}
              </p>
            </div>

            {/* WhatsApp Contact */}
            <div className="p-4 bg-green-50 rounded-xl border border-green-100">
              <a
                href={getWhatsAppHref('Hi Aqina SG, I have completed payment for my order.')}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-center text-sm font-semibold text-green-700 hover:text-green-800"
              >
                {ct('payment.whatsapp', {
                  phone: aqinaSiteConfig.contact.whatsappDisplay,
                }) || 'Send payment screenshot to WhatsApp for faster processing'}
              </a>
            </div>
          </div>

          <button
            onClick={onClose}
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
            <p className="text-sm text-charcoal/60">{product.name} — ${product.price}</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-charcoal/10 rounded-full transition-colors text-charcoal/40">
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
              <span className="font-bold text-charcoal">${product.price}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-charcoal/60">{ct('form.delivery') || 'Delivery Fee'}</span>
              <span className="font-bold text-green-600">{ct('form.free') || 'FREE'}</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
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
