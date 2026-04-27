"use client";

import { useTranslations } from "next-intl";
import Image from "next/image";
import { ShoppingCart } from "lucide-react";
import type { DisplayProduct } from "@/lib/product-service";

interface ProductCardProps {
  product: DisplayProduct;
  onBuyNow: (product: DisplayProduct) => void;
}

export function ProductCard({
  product,
  onBuyNow,
}: ProductCardProps) {
  const t = useTranslations("Index");

  return (
    <div className="group relative flex flex-col glass-panel rounded-3xl overflow-hidden hover:shadow-2xl transition-all hover:-translate-y-2 border border-charcoal/5">
      {product.popular && (
        <div className="absolute top-4 right-4 z-20 bg-secondary text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-tighter shadow-lg">
          {t("products.recommended")}
        </div>
      )}

      <div className="relative aspect-square w-full bg-ivory overflow-hidden">
        <Image
          src={product.image}
          alt={product.name}
          fill
          className="object-cover transition-transform duration-700 group-hover:scale-110"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-charcoal/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
      </div>

      <div className="p-6 flex flex-col flex-1 space-y-4">
        <div>
          <h3 className="text-xl font-bold text-charcoal">{product.name}</h3>
          <p className="text-sm text-charcoal/50">{product.label}</p>
        </div>

        <div className="flex items-baseline space-x-1">
          <span className="text-sm font-semibold text-charcoal/40">
            {t("products.currency")}
          </span>
          <span className="text-3xl font-bold text-secondary">
            ${product.price}
          </span>
        </div>

        <button
          onClick={() => onBuyNow(product)}
          className="w-full py-3 rounded-xl bg-charcoal text-ivory font-semibold hover:bg-primary transition-colors flex items-center justify-center space-x-2 group-active:scale-95 shadow-lg shadow-charcoal/10"
        >
          <ShoppingCart size={18} />
          <span>{t("products.buyNow")}</span>
        </button>
      </div>
    </div>
  );
}
