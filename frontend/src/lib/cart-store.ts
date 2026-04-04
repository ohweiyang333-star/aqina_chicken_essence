/**
 * Shopping Cart State Management with Zustand
 *
 * Provides cart state with localStorage persistence for the Aqina e-commerce platform.
 */

// Product interface based on the existing product structure
export interface Product {
  id: string;
  name: string;
  price: number;
  image: string;
  label: string;
  popular?: boolean;
}

// Cart item interface
export interface CartItem extends Product {
  quantity: number;
}

// Cart state interface
interface CartState {
  items: CartItem[];
  totalItems: number;
  totalPrice: number;

  // Actions
  addItem: (product: Product, quantity?: number) => void;
  removeItem: (productId: string) => void;
  updateQuantity: (productId: string, quantity: number) => void;
  clearCart: () => void;
  initializeCart: () => void;
}

// Helper to load cart from localStorage
const loadCartFromStorage = (): CartItem[] => {
  if (typeof window === 'undefined') return [];

  try {
    const stored = localStorage.getItem('aqina_cart');
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
};

// Helper to save cart to localStorage
const saveCartToStorage = (items: CartItem[]): void => {
  if (typeof window === 'undefined') return;

  try {
    localStorage.setItem('aqina_cart', JSON.stringify(items));
  } catch (error) {
    // Silently fail for localStorage errors
    // (e.g., when storage is full or in private browsing mode)
  }
};

// Helper to calculate totals
const calculateTotals = (items: CartItem[]) => {
  const totalItems = items.reduce((sum, item) => sum + item.quantity, 0);
  const totalPrice = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  return { totalItems, totalPrice };
};

// Create Zustand store
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      totalItems: 0,
      totalPrice: 0,

      // Initialize cart from localStorage (for SSR compatibility)
      initializeCart: () => {
        const stored = loadCartFromStorage();
        const { totalItems, totalPrice } = calculateTotals(stored);
        set({ items: stored, totalItems, totalPrice });
      },

      // Add item to cart
      addItem: (product: Product, quantity = 1) => {
        set((state) => {
          const existingItemIndex = state.items.findIndex(
            (item) => item.id === product.id
          );

          let newItems: CartItem[];

          if (existingItemIndex >= 0) {
            // Update quantity of existing item
            newItems = state.items.map((item, index) =>
              index === existingItemIndex
                ? { ...item, quantity: item.quantity + quantity }
                : item
            );
          } else {
            // Add new item
            newItems = [...state.items, { ...product, quantity }];
          }

          const { totalItems, totalPrice } = calculateTotals(newItems);
          saveCartToStorage(newItems);

          return { items: newItems, totalItems, totalPrice };
        });
      },

      // Remove item from cart
      removeItem: (productId: string) => {
        set((state) => {
          const newItems = state.items.filter((item) => item.id !== productId);
          const { totalItems, totalPrice } = calculateTotals(newItems);
          saveCartToStorage(newItems);

          return { items: newItems, totalItems, totalPrice };
        });
      },

      // Update item quantity
      updateQuantity: (productId: string, quantity: number) => {
        if (quantity <= 0) {
          // Remove item if quantity is 0 or negative
          get().removeItem(productId);
          return;
        }

        set((state) => {
          const newItems = state.items.map((item) =>
            item.id === productId ? { ...item, quantity } : item
          );

          const { totalItems, totalPrice } = calculateTotals(newItems);
          saveCartToStorage(newItems);

          return { items: newItems, totalItems, totalPrice };
        });
      },

      // Clear all items from cart
      clearCart: () => {
        set(() => {
          saveCartToStorage([]);
          return { items: [], totalItems: 0, totalPrice: 0 };
        });
      },
    }),
    {
      name: 'aqina-cart-storage', // localStorage key
      partialize: (state) => ({
        items: state.items,
      }),
    }
  )
);

export default useCartStore;
