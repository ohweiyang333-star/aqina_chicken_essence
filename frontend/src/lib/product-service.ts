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
import { IMAGES } from "./image-utils";
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

/**
 * DisplayProduct - 产品在 UI 中显示的格式
 * 这是经过 toDisplayProduct() 转换后的简化格式
 */
export interface DisplayProduct {
  id: string;
  name: string;
  price: number;
  image: string;
  label: string;
  popular?: boolean;
  badge?: string | null;
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
export function toDisplayProduct(product: Product, locale: string) {
  let image = product.imageUrl;
  const sizeOrId = (product.packSize || product.id || "").toLowerCase();
  
  if (sizeOrId.includes("1") || sizeOrId.includes("one") || sizeOrId.includes("一")) {
    image = IMAGES.products.box1;
  } else if (sizeOrId.includes("2") || sizeOrId.includes("two") || sizeOrId.includes("两") || sizeOrId.includes("二")) {
    image = IMAGES.products.box2;
  } else if (sizeOrId.includes("4") || sizeOrId.includes("four") || sizeOrId.includes("四")) {
    image = IMAGES.products.box4;
  } else if (sizeOrId.includes("6") || sizeOrId.includes("six") || sizeOrId.includes("六")) {
    image = IMAGES.products.box6;
  } else {
    image = IMAGES.products.boxMain;
  }

  return {
    id: product.id,
    name: product.name[locale as "en" | "zh"] || product.name.en,
    price: product.price,
    image: image,
    label: product.packSize,
    popular: product.isRecommended,
    badge: product.badge,
  };
}
