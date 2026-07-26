'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useEffect, useMemo, useState } from 'react';
import { IMAGES } from '@/lib/image-utils';
import {
  trackBeginCheckout,
  trackLandingFunnelEvent,
} from '@/lib/marketing-analytics';
import type { DisplayProduct } from '@/lib/product-display';

interface UseLandingProductsOptions {
  useStaticProducts?: boolean;
}

export default function useLandingProducts({
  useStaticProducts = false,
}: UseLandingProductsOptions = {}) {
  const t = useTranslations('Index');
  const locale = useLocale();
  const fallbackProducts: DisplayProduct[] = useMemo(
    () => [
      {
        id: 'pack1',
        name: t('products.items.pack1'),
        price: 47.9,
        image: IMAGES.products.box1,
        label: t('products.packSizes.pack1'),
        badge: t('products.badges.pack1'),
      },
      {
        id: 'pack2',
        name: t('products.items.pack2'),
        price: 79.8,
        image: IMAGES.products.box2,
        label: t('products.packSizes.pack2'),
        badge: t('products.badges.pack2'),
        popular: true,
      },
    ],
    [t],
  );
  const [selectedProduct, setSelectedProduct] = useState<DisplayProduct | null>(
    null,
  );
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [products, setProducts] = useState<DisplayProduct[]>(fallbackProducts);
  const [isLoading, setIsLoading] = useState(!useStaticProducts);

  useEffect(() => {
    if (useStaticProducts) {
      setProducts(fallbackProducts);
      setIsLoading(false);
      return;
    }

    async function loadProducts() {
      try {
        const {
          getProducts,
          resolveFixedPackKeyByMeta,
          toDisplayProduct,
        } = await import('@/lib/product-service');
        const fetchedProducts = await getProducts();
        if (fetchedProducts.length > 0) {
          const fallbackProductsByPack = new Map(
            fallbackProducts.map((product) => [product.id, product]),
          );
          const productsByPack = new Map<string, DisplayProduct>();
          fetchedProducts.forEach((product) => {
            const displayProduct = toDisplayProduct(product, locale);
            const packKey = resolveFixedPackKeyByMeta({
              id: displayProduct.id,
              packSize: displayProduct.label,
              nameEn: displayProduct.name,
              nameZh: displayProduct.name,
              price: displayProduct.price,
            });
            const fallbackProduct = fallbackProductsByPack.get(packKey);

            if (!fallbackProduct) {
              productsByPack.set(packKey, { ...displayProduct, id: packKey });
              return;
            }

            productsByPack.set(packKey, {
              ...displayProduct,
              // Key the product by its resolved pack, not the Firestore doc id: callers select
              // packs by `pack1` / `pack2` (and CheckoutModal re-derives the same key before
              // persisting the order). Leaving the raw doc id here made `find(p => p.id === tab)`
              // miss and silently fall back to products[0] — i.e. picking "2 boxes" checked out
              // 1 box.
              id: packKey,
              name:
                displayProduct.name === displayProduct.id
                  ? fallbackProduct.name
                  : displayProduct.name || fallbackProduct.name,
              label:
                displayProduct.label === packKey
                  ? fallbackProduct.label
                  : displayProduct.label,
              badge: displayProduct.badge ?? fallbackProduct.badge,
            });
          });

          fallbackProducts.forEach((fallbackProduct) => {
            if (!productsByPack.has(fallbackProduct.id)) {
              productsByPack.set(fallbackProduct.id, fallbackProduct);
            }
          });

          setProducts(
            ['pack1', 'pack2']
              .map((packKey) => productsByPack.get(packKey))
              .filter((product): product is DisplayProduct => Boolean(product)),
          );
        } else {
          setProducts(fallbackProducts);
        }
      } catch (error) {
        console.error('Error loading products:', error);
        setProducts(fallbackProducts);
      } finally {
        setIsLoading(false);
      }
    }

    loadProducts();
  }, [fallbackProducts, locale, useStaticProducts]);

  const handleBuyNow = (product: DisplayProduct) => {
    const productPayload = {
      source: 'product_offer',
      product_id: product.id,
      product_name: product.name,
      product_value: Number(product.price),
      package_label: product.label,
    };
    trackLandingFunnelEvent('product_buy_click', productPayload);
    trackBeginCheckout({
      productId: product.id,
      productName: product.name,
      value: Number(product.price),
      packageLabel: product.label,
    });
    trackLandingFunnelEvent('checkout_open', productPayload);
    setSelectedProduct(product);
    setIsCheckoutOpen(true);
  };

  const closeCheckout = () => {
    setIsCheckoutOpen(false);
  };

  return {
    products,
    isLoading,
    selectedProduct,
    isCheckoutOpen,
    handleBuyNow,
    closeCheckout,
  };
}
