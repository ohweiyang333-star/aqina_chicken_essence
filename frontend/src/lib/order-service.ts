import {
  collection,
  doc,
  getDocs,
  query,
  serverTimestamp,
  updateDoc,
  where,
} from 'firebase/firestore';
import { db } from './firebase';

export type OrderStatus = 'PENDING' | 'SHIPPED' | 'COMPLETED' | 'CANCELLED';
export type OrderPaymentStatus =
  | 'pending'
  | 'payment_submitted'
  | 'paid'
  | 'failed'
  | 'refunded';

export interface OrderLineItem {
  productId: string;
  productName: string;
  quantity: number;
  price: number;
}

export interface Order {
  id?: string;
  customerName: string;
  customerPhone: string;
  address: string;
  items: OrderLineItem[];
  subtotalAmount: number;
  shippingFee: number;
  boxCount: number;
  total: number;
  status: OrderStatus;
  paymentStatus: OrderPaymentStatus;
  paymentReceiptUrl?: string;
  source?: string;
  createdAt?: unknown;
}

export interface CreateCheckoutOrderInput {
  customerName: string;
  customerPhone: string;
  address: string;
  productId: string;
  receiptFile: File;
}

const ORDERS_COLLECTION = 'orders';
const PAYMENTS_COLLECTION = 'payments';

const orderStatusToBackend: Record<OrderStatus, string> = {
  PENDING: 'pending',
  SHIPPED: 'shipped',
  COMPLETED: 'delivered',
  CANCELLED: 'cancelled',
};

export const createOrder = async (order: CreateCheckoutOrderInput) => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const formData = new FormData();
  formData.append('customer_name', order.customerName);
  formData.append('customer_phone', order.customerPhone);
  formData.append('customer_address', order.address);
  formData.append('product_id', order.productId);
  formData.append('payment_receipt', order.receiptFile);

  const response = await fetch(`${baseUrl.replace(/\/$/, '')}/api/v1/orders/with-receipt`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || 'Order submission failed');
  }

  const payload = await response.json();
  return payload.order_id as string;
};

export const getOrders = async () => {
  try {
    const querySnapshot = await getDocs(collection(db, ORDERS_COLLECTION));
    return querySnapshot.docs
      .map((snapshot) => normalizeOrder(snapshot.id, snapshot.data()))
      .sort((a, b) => timestampMillis(b.createdAt) - timestampMillis(a.createdAt));
  } catch (error) {
    console.error('Error fetching orders:', error);
    throw error;
  }
};

export const updateOrderStatus = async (orderId: string, status: OrderStatus) => {
  try {
    const orderRef = doc(db, ORDERS_COLLECTION, orderId);
    await updateDoc(orderRef, {
      status,
      order_status: orderStatusToBackend[status],
      updated_at: serverTimestamp(),
    });
  } catch (error) {
    console.error('Error updating order status:', error);
    throw error;
  }
};

export const updateOrderPaymentStatus = async (
  orderId: string,
  paymentStatus: OrderPaymentStatus,
) => {
  try {
    const orderRef = doc(db, ORDERS_COLLECTION, orderId);
    await updateDoc(orderRef, {
      payment_status: paymentStatus,
      updated_at: serverTimestamp(),
    });

    const paymentsQuery = query(
      collection(db, PAYMENTS_COLLECTION),
      where('order_id', '==', orderId),
    );
    const paymentDocs = await getDocs(paymentsQuery);
    await Promise.all(
      paymentDocs.docs.map((paymentDoc) =>
        updateDoc(doc(db, PAYMENTS_COLLECTION, paymentDoc.id), {
          status: paymentStatus,
          updated_at: serverTimestamp(),
        }),
      ),
    );
  } catch (error) {
    console.error('Error updating payment status:', error);
    throw error;
  }
};

type RawRecord = Record<string, unknown>;

function normalizeOrder(id: string, data: RawRecord): Order {
  const customer = isRecord(data.customer) ? data.customer : {};
  const items = Array.isArray(data.items) ? data.items : [];
  const normalizedItems = items.map((rawItem) => {
    const item = isRecord(rawItem) ? rawItem : {};
    return {
      productId: String(item.productId || item.product_id || ''),
      productName: String(item.productName || item.product_name_zh || item.product_name || 'Order'),
      quantity: Number(item.quantity || 1),
      price: Number(item.price ?? item.unit_price ?? item.total_price ?? 0),
    };
  });
  const total = Number(data.total_amount ?? data.total ?? 0);
  const subtotalAmount = Number(data.subtotal_amount ?? data.subtotal ?? data.total ?? total);
  const shippingFee = Number(data.shipping_fee ?? Math.max(total - subtotalAmount, 0));

  return {
    id,
    customerName: String(data.customerName || customer.name || ''),
    customerPhone: String(data.customerPhone || customer.whatsapp || ''),
    address: String(data.address || customer.address || ''),
    items: normalizedItems,
    subtotalAmount,
    shippingFee,
    boxCount: Number(data.box_count ?? inferBoxCount(normalizedItems)),
    total,
    status: normalizeStatus(data.status || data.order_status),
    paymentStatus: normalizePaymentStatus(data.payment_status),
    paymentReceiptUrl:
      stringOrUndefined(data.payment_receipt_url) ?? stringOrUndefined(data.screenshot_url),
    source: stringOrUndefined(data.source) ?? 'landing_page',
    createdAt: data.createdAt || data.created_at,
  };
}

function isRecord(value: unknown): value is RawRecord {
  return typeof value === 'object' && value !== null;
}

function stringOrUndefined(value: unknown): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

function normalizeStatus(value: unknown): OrderStatus {
  const status = String(value || '').toLowerCase();
  if (status === 'shipped') return 'SHIPPED';
  if (status === 'completed' || status === 'delivered') return 'COMPLETED';
  if (status === 'cancelled') return 'CANCELLED';
  return 'PENDING';
}

function normalizePaymentStatus(value: unknown): OrderPaymentStatus {
  const status = String(value || 'pending').toLowerCase();
  if (status === 'paid') return 'paid';
  if (status === 'payment_submitted') return 'payment_submitted';
  if (status === 'failed') return 'failed';
  if (status === 'refunded') return 'refunded';
  return 'pending';
}

function inferBoxCount(items: OrderLineItem[]) {
  return items.reduce((sum, item) => {
    if (item.productId === 'pack6') return sum + 6;
    if (item.productId === 'pack4') return sum + 4;
    if (item.productId === 'pack2') return sum + 2;
    return sum + item.quantity;
  }, 0);
}

function timestampMillis(value: unknown) {
  if (!value) return 0;
  if (value instanceof Date) return value.getTime();
  if (typeof value === 'object' && value !== null && 'toMillis' in value) {
    return Number((value as { toMillis: () => number }).toMillis());
  }
  const parsed = Date.parse(String(value));
  return Number.isNaN(parsed) ? 0 : parsed;
}
