'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';
import { IMAGES } from '@/lib/image-utils';
import {
  getProducts,
  resolveFixedPackKeyByMeta,
  toDisplayProduct,
  type DisplayProduct,
} from '@/lib/product-service';

export default function useLandingProducts() {
  const t = useTranslations('Index');
  const locale = useLocale();
  const [selectedProduct, setSelectedProduct] = useState<DisplayProduct | null>(
    null,
  );
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [products, setProducts] = useState<DisplayProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadProducts() {
      const fallbackProducts: DisplayProduct[] = [
        {
          id: 'pack1',
          name: t('products.items.pack1'),
          price: 39.9,
          image: IMAGES.products.box1,
          label: t('products.packSizes.pack1'),
          badge: t('products.badges.pack1'),
        },
        {
          id: 'pack2',
          name: t('products.items.pack2'),
          price: 75.0,
          image: IMAGES.products.box2,
          label: t('products.packSizes.pack2'),
          badge: t('products.badges.pack2'),
          popular: true,
        },
        {
          id: 'pack4',
          name: t('products.items.pack4'),
          price: 149.0,
          image: IMAGES.products.box4,
          label: t('products.packSizes.pack4'),
          badge: t('products.badges.pack4'),
        },
        {
          id: 'pack6',
          name: t('products.items.pack6'),
          price: 219.0,
          image: IMAGES.products.box6,
          label: t('products.packSizes.pack6'),
          badge: t('products.badges.pack6'),
        },
      ];

      try {
        const fetchedProducts = await getProducts();
        if (fetchedProducts.length > 0) {
          const fallbackProductsByPack = new Map(
            fallbackProducts.map((product) => [product.id, product]),
          );
          setProducts(
            fetchedProducts.map((product) => {
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
                return displayProduct;
              }

              return {
                ...displayProduct,
                name:
                  displayProduct.name === displayProduct.id
                    ? fallbackProduct.name
                    : displayProduct.name || fallbackProduct.name,
                label:
                  displayProduct.label === packKey
                    ? fallbackProduct.label
                    : displayProduct.label,
                badge: displayProduct.badge ?? fallbackProduct.badge,
              };
            }),
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
  }, [locale, t]);

  const handleBuyNow = (product: DisplayProduct) => {
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
