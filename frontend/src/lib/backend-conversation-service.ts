import { apiClient } from "@/lib/api-client";

export type MarketingInboxChannel = "messenger" | "whatsapp";
export type MarketingInboxFilter = "all" | MarketingInboxChannel;
export type MarketingTag = "lead_cold" | "qualified_warm" | "cart_hot" | "handoff_pending";

export interface MarketingInboxMessage {
  message_id: string;
  direction: "inbound" | "outbound";
  role: string;
  text: string;
  message_type?: string;
  delivery_status?: string;
  provider_message_id?: string | null;
  media_url?: string | null;
  media_content_type?: string | null;
  media_filename?: string | null;
  source?: string;
  created_at?: string;
  error_message?: string;
}

export interface MarketingAcquisition {
  source: string;
  ref?: string | null;
  ad_id?: string | null;
  post_id?: string | null;
  raw_referral?: Record<string, unknown> | null;
}

export interface MarketingConversationSummary {
  conversation_id: string;
  contact_id: string;
  channel: MarketingInboxChannel;
  customer_name: string;
  platform_id: string;
  current_tag: MarketingTag | "";
  marketing_status: string;
  automation_paused: boolean;
  acquisition: MarketingAcquisition;
  last_message_at?: string;
  latest_message?: MarketingInboxMessage | null;
  window: {
    is_open: boolean;
    expires_at?: string | null;
  };
  orders: Array<{
    order_id: string;
    payment_status?: string;
    order_status?: string;
    total_amount?: number;
  }>;
}

export interface MarketingConversationDetail {
  conversation: MarketingConversationSummary;
  contact: Record<string, unknown> & { contact_id: string };
  messages: MarketingInboxMessage[];
  orders: MarketingConversationSummary["orders"];
  window: MarketingConversationSummary["window"];
}

export async function listMarketingConversations(channel: MarketingInboxFilter = "all") {
  const response = await apiClient.get<{ items: MarketingConversationSummary[] }>(
    "/api/v1/marketing/conversations",
    { channel },
  );
  return response.items;
}

export async function getMarketingConversation(conversationId: string) {
  return apiClient.get<MarketingConversationDetail>(
    `/api/v1/marketing/conversations/${conversationId}`,
  );
}

export async function sendMarketingConversationText(conversationId: string, text: string) {
  return apiClient.post<{ status: string; provider_message_id?: string; message_id?: string }>(
    `/api/v1/marketing/conversations/${conversationId}/messages`,
    { text },
  );
}

export async function sendMarketingConversationImage(
  conversationId: string,
  image: File,
  caption?: string,
) {
  const formData = new FormData();
  formData.append("image", image);
  if (caption?.trim()) {
    formData.append("caption", caption.trim());
  }
  return apiClient.postForm<{
    status: string;
    provider_message_id?: string;
    message_id?: string;
    media_url?: string;
  }>(`/api/v1/marketing/conversations/${conversationId}/images`, formData);
}

export async function updateMarketingConversationAutomation(
  conversationId: string,
  paused: boolean,
  reason?: string,
) {
  return apiClient.post<{ status: string }>(
    `/api/v1/marketing/conversations/${conversationId}/automation`,
    { paused, reason },
  );
}

export async function updateMarketingContactTag(contactId: string, currentTag: MarketingTag) {
  return apiClient.post<{ status: string; contact_id: string; current_tag: MarketingTag }>(
    `/api/v1/marketing/contacts/${contactId}/tag`,
    { current_tag: currentTag },
  );
}
