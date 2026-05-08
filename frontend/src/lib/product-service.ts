/**
 * Product Service for Firestore operations
 */

import {
  collection,
  getDocs,
  doc,
  getDoc,
  query,
  orderBy,
} from "firebase/firestore";
import { db } from "./firebase";
import {
  FIXED_PRODUCT_IMAGES,
  resolveFixedPackKeyByMeta,
  type DisplayProduct,
} from "./product-display";
export type { DisplayProduct, FixedPackKey } from "./product-display";
export {
  resolveFixedPackKeyByMeta,
  resolveFixedProductImageByMeta,
} from "./product-display";

export interface Product {
  id: string;
  name: {
    en: string;
    zh: string;
  };
  nameShort: {
    en: string;
    zh: string;
  };
  description: {
    en: string;
    zh: string;
  };
  price: number;
  originalPrice: number | null;
  imageUrl: string;
  packSize: string;
  badge: string | null;
  isRecommended: boolean;
  category: string;
}

type SupportedLocale = "en" | "zh";
type LocalizedField =
  | Partial<Record<SupportedLocale, string>>
  | string
  | null
  | undefined;

type ProductRecord = Partial<Omit<Product, "name" | "nameShort" | "description">> & {
  id: string;
  name?: LocalizedField;
  nameShort?: LocalizedField;
  description?: LocalizedField;
  product_name?: string;
  product_name_zh?: string;
  name_en?: string;
  name_zh?: string;
  pack_size?: string;
  is_recommended?: boolean;
};

function normalizeLocale(locale: string): SupportedLocale {
  return locale === "zh" ? "zh" : "en";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function pickString(...values: unknown[]): string | undefined {
  for (const value of values) {
    if (typeof value === "string" && value.trim().length > 0) {
      return value.trim();
    }
  }

  return undefined;
}

function getLocalizedText(
  value: LocalizedField,
  locale: SupportedLocale,
): string | undefined {
  if (typeof value === "string") {
    return pickString(value);
  }

  if (!isRecord(value)) {
    return undefined;
  }

  return pickString(value[locale], value.en, value.zh);
}

/**
 * Get all products from Firestore
 */
export async function getProducts(): Promise<Product[]> {
  try {
    const q = query(collection(db, "products"), orderBy("price"));
    const querySnapshot = await getDocs(q);

    const products: Product[] = [];
    querySnapshot.forEach((doc) => {
      const data = doc.data() as Omit<Product, "id">;
      products.push({
        id: doc.id,
        ...data,
      });
    });

    return products;
  } catch (error) {
    console.error("Error fetching products:", error);
    return [];
  }
}

/**
 * Get a single product by ID
 */
export async function getProductById(id: string): Promise<Product | null> {
  try {
    const docRef = doc(db, "products", id);
    const docSnap = await getDoc(docRef);

    if (docSnap.exists()) {
      const data = docSnap.data() as Omit<Product, "id">;
      return {
        id: docSnap.id,
        ...data,
      };
    }

    return null;
  } catch (error) {
    console.error("Error fetching product:", error);
    return null;
  }
}

/**
 * Transform Firestore product to display format for legacy code
 */
export function toDisplayProduct(product: Product, locale: string): DisplayProduct {
  const rawProduct = product as ProductRecord;
  const safeLocale = normalizeLocale(locale);
  const price = Number(rawProduct.price ?? 0);
  const nameEn =
    pickString(
      getLocalizedText(rawProduct.name, "en"),
      getLocalizedText(rawProduct.nameShort, "en"),
      rawProduct.name_en,
      rawProduct.product_name,
      rawProduct.id,
    ) ?? rawProduct.id;
  const nameZh =
    pickString(
      getLocalizedText(rawProduct.name, "zh"),
      getLocalizedText(rawProduct.nameShort, "zh"),
      rawProduct.name_zh,
      rawProduct.product_name_zh,
      nameEn,
    ) ?? nameEn;
  const packSize = pickString(rawProduct.packSize, rawProduct.pack_size) ?? "";
  const packKey = resolveFixedPackKeyByMeta({
    id: rawProduct.id,
    packSize,
    nameEn,
    nameZh,
    price,
  });
  const image = FIXED_PRODUCT_IMAGES[packKey];

  return {
    id: rawProduct.id,
    name: safeLocale === "zh" ? nameZh : nameEn,
    price,
    image,
    label: packSize || packKey,
    popular: Boolean(rawProduct.isRecommended ?? rawProduct.is_recommended),
    badge: pickString(rawProduct.badge) ?? null,
  };
}
