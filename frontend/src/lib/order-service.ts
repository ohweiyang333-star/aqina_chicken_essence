import {
  collection,
  doc,
  getDoc,
  getDocs,
  query,
  serverTimestamp,
  updateDoc,
  where,
} from 'firebase/firestore';
import { db } from './firebase';
import { apiClient } from './api-client';
import type { MarketingServerEventContext } from './marketing-analytics';

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

export interface GiftChoice {
  code?: string;
  name?: string;
  weight?: string;
  displayName: string;
}

export interface PaymentVerification {
  status: 'ok' | 'warning' | 'unavailable';
  expectedAmount?: number;
  extractedAmount?: number;
  amountMatch: boolean;
  referenceNumber?: string;
  referenceNormalized?: string;
  duplicateDetected: boolean;
  duplicateOrderIds: string[];
  duplicatePaymentIds: string[];
  warnings: string[];
  confidence?: number;
  currency?: string;
  recipientReference?: string;
  paymentDatetime?: string;
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
  giftChoice?: GiftChoice;
  total: number;
  status: OrderStatus;
  paymentStatus: OrderPaymentStatus;
  paymentReceiptUrl?: string;
  transactionId?: string;
  paymentVerification?: PaymentVerification;
  riskFlags: string[];
  notes?: string;
  customerRequestRemark?: string;
  source?: string;
  sourceChannel?: string;
  marketingContactId?: string;
  conversationId?: string;
  channel?: string;
  checkoutSessionId?: string;
  utmSource?: string;
  utmCampaign?: string;
  metaCampaignId?: string;
  metaAdsetId?: string;
  metaAdId?: string;
  expectedShipDate?: string;
  lastCustomerContactAt?: unknown;
  lastCustomerContactMethod?: string;
  createdAt?: unknown;
}

export interface OrderContactTemplate {
  name: string;
  languageCode: string;
  category?: string;
}

export interface OrderContactContext {
  orderId: string;
  sourceLabel: string;
  sourceChannel?: string;
  customerName: string;
  rawWhatsApp: string;
  normalizedWhatsApp?: string;
  whatsappDraftUrl?: string;
  contactId?: string;
  conversationId?: string;
  conversationUrl?: string;
  windowIsOpen: boolean;
  windowExpiresAt?: string;
  backendSendMethod?: 'free_text' | 'template';
  approvedTemplates: OrderContactTemplate[];
}

export interface SendOrderWhatsAppNotificationInput {
  expectedShipDate: string;
  message: string;
  templateName?: string;
  languageCode?: string;
  bodyVariables?: string[];
}

export interface SendOrderWhatsAppNotificationResult {
  status: 'sent';
  method: 'free_text' | 'template';
  orderId: string;
  expectedShipDate: string;
  conversationId: string;
  providerMessageId?: string;
  messageId?: string;
}

export interface CreateCheckoutOrderInput {
  customerName: string;
  customerPhone: string;
  address: string;
  productId: string;
  receiptFile: File;
  giftChoice?: string;
  marketing?: MarketingServerEventContext | null;
}

export type CheckoutOrderErrorCode =
  | 'nameRequired'
  | 'phoneInvalid'
  | 'addressInvalid'
  | 'receiptRequired'
  | 'receiptInvalidType'
  | 'receiptTooLarge'
  | 'unknownPackage'
  | 'submitError';

export class CheckoutOrderError extends Error {
  code: CheckoutOrderErrorCode;

  constructor(message: string, code: CheckoutOrderErrorCode = 'submitError') {
    super(message);
    this.name = 'CheckoutOrderError';
    this.code = code;
  }
}

const ORDERS_COLLECTION = 'orders';
const MARKETING_CONTACTS_COLLECTION = 'marketing_contacts';
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
  if (order.giftChoice) {
    formData.append('gift_choice', order.giftChoice);
  }
  formData.append('payment_receipt', order.receiptFile);
  appendMarketingEventContext(formData, order.marketing);

  const response = await fetch(`${baseUrl.replace(/\/$/, '')}/api/v1/orders/with-receipt`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw parseCheckoutOrderError(payload);
  }

  const payload = await response.json();
  return payload.order_id as string;
};

function appendMarketingEventContext(
  formData: FormData,
  marketing: MarketingServerEventContext | null | undefined,
) {
  if (!marketing) return;

  formData.append('marketing_consent', marketing.marketing_consent);
  formData.append('marketing_event_id', marketing.marketing_event_id);
  formData.append('event_source_url', marketing.event_source_url);
  formData.append('page_path', marketing.page_path);

  if (marketing.landing_version) {
    formData.append('landing_version', marketing.landing_version);
  }
  if (marketing.language) {
    formData.append('language', marketing.language);
  }
  if (marketing.marketing_fbp) {
    formData.append('marketing_fbp', marketing.marketing_fbp);
  }
  if (marketing.marketing_fbc) {
    formData.append('marketing_fbc', marketing.marketing_fbc);
  }
}

function parseCheckoutOrderError(payload: unknown): CheckoutOrderError {
  const detail = isRecord(payload) ? payload.detail : undefined;

  if (typeof detail === 'string') {
    return checkoutOrderErrorFromMessage(detail);
  }

  if (Array.isArray(detail)) {
    const firstDetail = detail.find(isRecord);
    const loc = Array.isArray(firstDetail?.loc)
      ? firstDetail.loc.map((part) => String(part))
      : [];
    const field = loc[loc.length - 1];

    if (field === 'customer_name') {
      return new CheckoutOrderError('Customer name is required', 'nameRequired');
    }
    if (field === 'customer_phone') {
      return new CheckoutOrderError('WhatsApp phone must contain 8 to 20 digits', 'phoneInvalid');
    }
    if (field === 'customer_address') {
      return new CheckoutOrderError('Delivery address must be 10 to 500 characters', 'addressInvalid');
    }
    if (field === 'payment_receipt') {
      return new CheckoutOrderError('Please upload your PayNow payment receipt before submitting.', 'receiptRequired');
    }
  }

  return new CheckoutOrderError('Order submission failed');
}

function checkoutOrderErrorFromMessage(message: string): CheckoutOrderError {
  if (message.includes('Customer name is required')) {
    return new CheckoutOrderError(message, 'nameRequired');
  }
  if (message.includes('WhatsApp phone')) {
    return new CheckoutOrderError(message, 'phoneInvalid');
  }
  if (message.includes('Delivery address')) {
    return new CheckoutOrderError(message, 'addressInvalid');
  }
  if (message.includes('Receipt must be JPG, PNG, or WebP')) {
    return new CheckoutOrderError(message, 'receiptInvalidType');
  }
  if (message.includes('Receipt file is too large')) {
    return new CheckoutOrderError(message, 'receiptTooLarge');
  }
  if (message.includes('Receipt file is empty')) {
    return new CheckoutOrderError(message, 'receiptRequired');
  }
  if (message.includes('Unknown package')) {
    return new CheckoutOrderError(message, 'unknownPackage');
  }

  return new CheckoutOrderError(message || 'Order submission failed');
}

export const getOrders = async () => {
  try {
    const querySnapshot = await getDocs(collection(db, ORDERS_COLLECTION));
    const orders = querySnapshot.docs
      .map((snapshot) => normalizeOrder(snapshot.id, snapshot.data()))
      .sort((a, b) => timestampMillis(b.createdAt) - timestampMillis(a.createdAt));
    return attachOrderSourceChannels(orders);
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

export const getOrderContactContext = async (
  orderId: string,
): Promise<OrderContactContext> => {
  const payload = await apiClient.get<RawRecord>(
    `/api/v1/orders/${orderId}/contact-context`,
  );
  return normalizeOrderContactContext(payload);
};

export const sendOrderWhatsAppNotification = async (
  orderId: string,
  input: SendOrderWhatsAppNotificationInput,
): Promise<SendOrderWhatsAppNotificationResult> => {
  const payload = await apiClient.post<RawRecord>(
    `/api/v1/orders/${orderId}/whatsapp-notifications`,
    {
      expected_ship_date: input.expectedShipDate,
      message: input.message,
      template_name: input.templateName,
      language_code: input.languageCode || 'en_US',
      body_variables: input.bodyVariables || [],
    },
  );

  return {
    status: 'sent',
    method: payload.method === 'template' ? 'template' : 'free_text',
    orderId: String(payload.order_id || orderId),
    expectedShipDate: String(payload.expected_ship_date || input.expectedShipDate),
    conversationId: String(payload.conversation_id || ''),
    providerMessageId: stringOrUndefined(payload.provider_message_id),
    messageId: stringOrUndefined(payload.message_id),
  };
};

type RawRecord = Record<string, unknown>;

function normalizeOrder(id: string, data: RawRecord): Order {
  const customer = isRecord(data.customer) ? data.customer : {};
  const items = Array.isArray(data.items) ? data.items : [];
  const rawCustomerName = String(data.customerName || customer.name || '');
  const legacyGift = parseLegacyGiftFromCustomerName(rawCustomerName);
  const giftChoice =
    normalizeGiftChoice(data.gift_choice) ??
    normalizeGiftChoice(data.giftChoice) ??
    legacyGift.giftChoice;
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
    customerName: legacyGift.customerName,
    customerPhone: String(data.customerPhone || customer.whatsapp || ''),
    address: String(data.address || customer.address || ''),
    items: normalizedItems,
    subtotalAmount,
    shippingFee,
    boxCount: Number(data.box_count ?? inferBoxCount(normalizedItems)),
    giftChoice,
    total,
    status: normalizeStatus(data.status || data.order_status),
    paymentStatus: normalizePaymentStatus(data.payment_status),
    paymentReceiptUrl:
      stringOrUndefined(data.payment_receipt_url) ?? stringOrUndefined(data.screenshot_url),
    transactionId: stringOrUndefined(data.transaction_id),
    paymentVerification: normalizePaymentVerification(data.payment_verification),
    riskFlags: normalizeStringArray(data.risk_flags),
    notes: stringOrUndefined(data.notes),
    customerRequestRemark:
      stringOrUndefined(data.customer_request_remark) ?? stringOrUndefined(data.notes),
    source: stringOrUndefined(data.source) ?? 'landing_page',
    sourceChannel: stringOrUndefined(data.source_channel),
    marketingContactId: stringOrUndefined(data.marketing_contact_id),
    conversationId: stringOrUndefined(data.conversation_id),
    channel: stringOrUndefined(data.channel),
    checkoutSessionId: stringOrUndefined(data.checkout_session_id),
    utmSource: stringOrUndefined(data.utm_source),
    utmCampaign: stringOrUndefined(data.utm_campaign),
    metaCampaignId: stringOrUndefined(data.meta_campaign_id),
    metaAdsetId: stringOrUndefined(data.meta_adset_id),
    metaAdId: stringOrUndefined(data.meta_ad_id),
    expectedShipDate: stringOrUndefined(data.expected_ship_date),
    lastCustomerContactAt: data.last_customer_contact_at,
    lastCustomerContactMethod: stringOrUndefined(data.last_customer_contact_method),
    createdAt: data.createdAt || data.created_at,
  };
}

function parseLegacyGiftFromCustomerName(customerName: string) {
  const trimmedName = customerName.trim();
  const match = trimmedName.match(/^(.*?)\s*[\(（]\s*(?:赠|贈|gift)\s*[:：]\s*([^)）]+)\s*[\)）]\s*$/i);
  if (!match) {
    return { customerName: trimmedName, giftChoice: undefined as GiftChoice | undefined };
  }

  const cleanName = match[1]?.trim() || trimmedName;
  const giftText = match[2]?.trim() || '';
  return {
    customerName: cleanName,
    giftChoice: giftText ? { displayName: giftText } : undefined,
  };
}

function normalizeGiftChoice(value: unknown): GiftChoice | undefined {
  if (typeof value === 'string') {
    const displayName = value.trim();
    return displayName ? { displayName } : undefined;
  }
  if (!isRecord(value)) return undefined;

  const code = stringOrUndefined(value.code);
  const name = stringOrUndefined(value.name);
  const weight = stringOrUndefined(value.weight);
  const displayName =
    stringOrUndefined(value.display_name) ??
    stringOrUndefined(value.displayName) ??
    [name, weight].filter(Boolean).join(' ');

  if (!displayName) return undefined;
  return { code, name, weight, displayName };
}

function normalizeOrderContactContext(data: RawRecord): OrderContactContext {
  const templates = Array.isArray(data.approved_templates)
    ? data.approved_templates
        .map((rawTemplate) => {
          const template = isRecord(rawTemplate) ? rawTemplate : {};
          return {
            name: String(template.name || ''),
            languageCode: String(template.language_code || 'en_US'),
            category: stringOrUndefined(template.category),
          };
        })
        .filter((template) => template.name.length > 0)
    : [];

  const sendMethod = String(data.backend_send_method || '');

  return {
    orderId: String(data.order_id || ''),
    sourceLabel: String(data.source_label || 'Landing Checkout'),
    sourceChannel: stringOrUndefined(data.source_channel),
    customerName: String(data.customer_name || ''),
    rawWhatsApp: String(data.raw_whatsapp || ''),
    normalizedWhatsApp: stringOrUndefined(data.normalized_whatsapp),
    whatsappDraftUrl: stringOrUndefined(data.whatsapp_draft_url),
    contactId: stringOrUndefined(data.contact_id),
    conversationId: stringOrUndefined(data.conversation_id),
    conversationUrl: stringOrUndefined(data.conversation_url),
    windowIsOpen: Boolean(data.window_is_open),
    windowExpiresAt: stringOrUndefined(data.window_expires_at),
    backendSendMethod:
      sendMethod === 'free_text' || sendMethod === 'template' ? sendMethod : undefined,
    approvedTemplates: templates,
  };
}

async function attachOrderSourceChannels(orders: Order[]) {
  const contactIds = Array.from(
    new Set(
      orders
        .filter((order) => order.source === 'marketing_chatbot' && !order.sourceChannel)
        .map((order) => order.marketingContactId)
        .filter((contactId): contactId is string => Boolean(contactId)),
    ),
  );

  if (contactIds.length === 0) return orders;

  const entries = await Promise.all(
    contactIds.map(async (contactId) => {
      try {
        const snapshot = await getDoc(
          doc(db, MARKETING_CONTACTS_COLLECTION, contactId),
        );
        const data = snapshot.exists() ? snapshot.data() : null;
        return [contactId, stringOrUndefined(data?.channel)] as const;
      } catch (error) {
        console.warn('Failed to fetch order source channel:', contactId, error);
        return [contactId, undefined] as const;
      }
    }),
  );
  const channelByContactId = new Map(entries);

  return orders.map((order) => {
    if (order.sourceChannel || !order.marketingContactId) return order;
    const sourceChannel = channelByContactId.get(order.marketingContactId);
    return sourceChannel ? { ...order, sourceChannel } : order;
  });
}

function isRecord(value: unknown): value is RawRecord {
  return typeof value === 'object' && value !== null;
}

function stringOrUndefined(value: unknown): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

function numberOrUndefined(value: unknown): number | undefined {
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : undefined;
}

function normalizeStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
}

function normalizePaymentVerification(value: unknown): PaymentVerification | undefined {
  if (!isRecord(value)) return undefined;
  const status = String(value.status || '').toLowerCase();
  const normalizedStatus: PaymentVerification['status'] =
    status === 'ok' || status === 'warning' || status === 'unavailable'
      ? status
      : 'warning';

  return {
    status: normalizedStatus,
    expectedAmount: numberOrUndefined(value.expected_amount),
    extractedAmount: numberOrUndefined(value.extracted_amount),
    amountMatch: Boolean(value.amount_match),
    referenceNumber: stringOrUndefined(value.reference_number),
    referenceNormalized: stringOrUndefined(value.reference_normalized),
    duplicateDetected: Boolean(value.duplicate_detected),
    duplicateOrderIds: normalizeStringArray(value.duplicate_order_ids),
    duplicatePaymentIds: normalizeStringArray(value.duplicate_payment_ids),
    warnings: normalizeStringArray(value.warnings),
    confidence: numberOrUndefined(value.confidence),
    currency: stringOrUndefined(value.currency),
    recipientReference: stringOrUndefined(value.recipient_reference),
    paymentDatetime: stringOrUndefined(value.payment_datetime),
  };
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
