import { apiClient } from "@/lib/api-client";

export interface EscalationRecord {
  escalation_id: string;
  contact_id: string;
  conversation_id?: string | null;
  reason: string;
  latest_customer_message: string;
  status: "open" | "acknowledged" | "resolved";
  private_whatsapp_number: string;
  template_name: string;
  template_variables: string[];
  notified_at?: string;
  resolved_at?: string | null;
}

export interface MarketingCheckoutPayload {
  order_id: string;
  payment_method: "paynow";
  payment_status: string;
  order_status: string;
  total_amount: number;
  customer_name: string;
  customer_whatsapp: string;
  delivery_address: string;
  items: Array<{
    product_id: string;
    product_name: string;
    product_name_zh: string;
    quantity: number;
    unit_price: number;
    total_price: number;
  }>;
  paynow: {
    enabled: boolean;
    payment_qr_image: string;
    payment_qr_alt: string;
    payment_reference_prefix: string;
    payment_note: string;
  };
  checkout_url: string;
  package_code?: string | null;
}

export async function listEscalations(): Promise<EscalationRecord[]> {
  const response = await apiClient.get<{ items: EscalationRecord[] }>(
    "/api/v1/marketing/escalations",
  );
  return response.items;
}

export async function acknowledgeEscalation(escalationId: string) {
  return apiClient.post<{ status: string }>(
    `/api/v1/marketing/escalations/${escalationId}/acknowledge`,
    {},
  );
}

export async function resolveEscalation(escalationId: string) {
  return apiClient.post<{ status: string }>(
    `/api/v1/marketing/escalations/${escalationId}/resolve`,
    {},
  );
}

export async function getMarketingCheckout(token: string) {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const response = await fetch(`${baseUrl.replace(/\/$/, "")}/api/v1/marketing/checkout/${token}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to load checkout payload");
  }
  return (await response.json()) as MarketingCheckoutPayload;
}
