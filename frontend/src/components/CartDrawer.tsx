'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { X, Plus, Minus, ShoppingBag, ArrowRight } from 'lucide-react';
import useCartStore from '@/lib/cart-store';

interface CartDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onCheckout: () => void;
}

export default function CartDrawer({ isOpen, onClose, onCheckout }: CartDrawerProps) {
  const t = useTranslations('Index.Cart');
  const { items, totalItems, totalPrice, updateQuantity, removeItem } = useCartStore();

  const handleQuantityChange = (productId: string, newQuantity: number) => {
    updateQuantity(productId, newQuantity);
  };

  const handleRemoveItem = (productId: string) => {
    removeItem(productId);
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/50 z-50 transition-opacity duration-300 ${
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-full max-w-md bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-charcoal/10">
            <div className="flex items-center gap-3">
              <div className="relative">
                <ShoppingBag className="w-6 h-6 text-charcoal" />
                {totalItems > 0 && (
                  <span className="absolute -top-2 -right-2 bg-primary text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center">
                    {totalItems}
                  </span>
                )}
              </div>
              <h2 className="text-xl font-bold text-charcoal">{t('title')}</h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-charcoal/5 rounded-full transition-colors"
              aria-label="Close cart"
            >
              <X className="w-6 h-6 text-charcoal" />
            </button>
          </div>

          {/* Cart Items */}
          <div className="flex-1 overflow-y-auto p-6">
            {items.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <ShoppingBag className="w-16 h-16 text-charcoal/20 mb-4" />
                <p className="text-charcoal/60 text-lg">{t('empty')}</p>
                <button
                  onClick={onClose}
                  className="mt-4 text-primary font-semibold hover:underline"
                >
                  {t('continueShopping')}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className="flex gap-4 p-4 bg-ivory rounded-2xl border border-charcoal/5"
                  >
                    {/* Product Image */}
                    <div className="relative w-20 h-20 flex-shrink-0 bg-white rounded-xl overflow-hidden">
                      <Image
                        src={item.image}
                        alt={item.name}
                        fill
                        className="object-cover"
                      />
                    </div>

                    {/* Product Details */}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-charcoal truncate">{item.name}</h3>
                      <p className="text-sm text-charcoal/60">{item.label}</p>

                      {/* Price */}
                      <p className="text-lg font-bold text-primary mt-1">
                        SGD {item.price.toFixed(2)}
                      </p>
                    </div>

                    {/* Quantity Controls */}
                    <div className="flex flex-col items-end justify-between">
                      <button
                        onClick={() => handleRemoveItem(item.id)}
                        className="p-1 hover:bg-red-50 rounded transition-colors"
                        aria-label="Remove item"
                      >
                        <X className="w-4 h-4 text-red-500" />
                      </button>

                      <div className="flex items-center gap-2 bg-white rounded-lg border border-charcoal/10">
                        <button
                          onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                          className="p-1 hover:bg-charcoal/5 rounded transition-colors"
                          aria-label="Decrease quantity"
                          disabled={item.quantity <= 1}
                        >
                          <Minus className="w-4 h-4 text-charcoal" />
                        </button>
                        <span className="w-8 text-center font-semibold text-charcoal">
                          {item.quantity}
                        </span>
                        <button
                          onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                          className="p-1 hover:bg-charcoal/5 rounded transition-colors"
                          aria-label="Increase quantity"
                        >
                          <Plus className="w-4 h-4 text-charcoal" />
                        </button>
                      </div>

                      {/* Item Total */}
                      <p className="text-sm font-semibold text-charcoal mt-2">
                        SGD {(item.price * item.quantity).toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {items.length > 0 && (
            <div className="border-t border-charcoal/10 p-6 bg-ivory">
              {/* Subtotal */}
              <div className="flex items-center justify-between mb-4">
                <span className="text-charcoal/60">{t('subtotal')}</span>
                <span className="text-2xl font-bold text-charcoal">
                  SGD {totalPrice.toFixed(2)}
                </span>
              </div>

              {/* Free Shipping Notice */}
              {totalPrice >= 70 && (
                <div className="flex items-center gap-2 p-3 bg-green-50 text-green-700 rounded-lg mb-4 text-sm">
                  ✓ {t('freeShipping')}
                </div>
              )}

              {/* Checkout Button */}
              <button
                onClick={onCheckout}
                className="w-full py-4 bg-primary text-white font-bold rounded-xl hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 shadow-lg"
              >
                {t('checkout')}
                <ArrowRight className="w-5 h-5" />
              </button>

              {/* Continue Shopping */}
              <button
                onClick={onClose}
                className="w-full py-3 mt-2 text-charcoal/60 hover:text-charcoal transition-colors text-sm font-medium"
              >
                {t('continueShopping')}
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
