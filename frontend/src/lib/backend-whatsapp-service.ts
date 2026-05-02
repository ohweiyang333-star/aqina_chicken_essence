import { apiClient } from "@/lib/api-client";

export interface WhatsAppMessage {
  message_id: string;
  direction: "inbound" | "outbound";
  role: string;
  text: string;
  message_type?: string;
  delivery_status?: string;
  provider_message_id?: string | null;
  source?: string;
  created_at?: string;
  error_message?: string;
}

export interface WhatsAppConversationSummary {
  conversation_id: string;
  contact_id: string;
  channel: "whatsapp";
  customer_name: string;
  wa_id: string;
  current_tag: string;
  automation_paused: boolean;
  marketing_status: string;
  last_message_at?: string;
  latest_message?: WhatsAppMessage | null;
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

export interface WhatsAppConversationDetail {
  conversation: WhatsAppConversationSummary;
  contact: Record<string, unknown>;
  messages: WhatsAppMessage[];
  orders: WhatsAppConversationSummary["orders"];
  window: WhatsAppConversationSummary["window"];
}

export interface WhatsAppTemplate {
  template_id: string;
  name: string;
  language_code: string;
  category: string;
  status: string;
  components: Array<Record<string, unknown>>;
  updated_at?: string;
}

export interface WhatsAppHealth {
  ready: boolean;
  config: {
    access_token: boolean;
    phone_number_id: boolean;
    business_account_id: boolean;
    cloud_tasks_enabled: boolean;
    campaign_queue: string;
  };
  phone?: Record<string, unknown> | null;
  phone_error?: string | null;
  local_template_count: number;
}

export interface WhatsAppCampaignPreview {
  eligible_count: number;
  skipped_opt_out_count: number;
  window_closed_count: number;
  missing_variable_count: number;
  recipients: Array<{
    contact_id: string;
    conversation_id?: string | null;
    wa_id: string;
    customer_name: string;
    current_tag: string;
    window_open: boolean;
  }>;
}

export interface WhatsAppCampaign {
  campaign_id: string;
  name: string;
  template_name: string;
  language_code: string;
  body_variables: string[];
  audience_tags: string[];
  status: string;
  eligible_count: number;
  queued_count: number;
  sent_count: number;
  delivered_count?: number;
  read_count?: number;
  failed_count: number;
  created_at?: string;
}

export interface WhatsAppCampaignDetail {
  campaign: WhatsAppCampaign;
  recipients: Array<{
    recipient_id: string;
    contact_id: string;
    wa_id: string;
    customer_name: string;
    status: string;
    error_code?: number | null;
    error_message?: string | null;
    provider_message_id?: string | null;
  }>;
}

export interface WhatsAppCampaignPayload {
  name: string;
  template_name: string;
  language_code: string;
  body_variables: string[];
  audience_tags: string[];
}

export async function getWhatsAppHealth(): Promise<WhatsAppHealth> {
  return apiClient.get<WhatsAppHealth>("/api/v1/marketing/whatsapp/health");
}

export async function listWhatsAppConversations() {
  const response = await apiClient.get<{ items: WhatsAppConversationSummary[] }>(
    "/api/v1/marketing/whatsapp/conversations",
  );
  return response.items;
}

export async function getWhatsAppConversation(conversationId: string) {
  return apiClient.get<WhatsAppConversationDetail>(
    `/api/v1/marketing/whatsapp/conversations/${conversationId}`,
  );
}

export async function sendWhatsAppText(conversationId: string, text: string) {
  return apiClient.post<{ status: string; provider_message_id?: string }>(
    `/api/v1/marketing/whatsapp/conversations/${conversationId}/messages`,
    { text },
  );
}

export async function sendWhatsAppTemplate(
  conversationId: string,
  templateName: string,
  languageCode: string,
  bodyVariables: string[],
) {
  return apiClient.post<{ status: string; provider_message_id?: string }>(
    `/api/v1/marketing/whatsapp/conversations/${conversationId}/templates`,
    {
      template_name: templateName,
      language_code: languageCode,
      body_variables: bodyVariables,
    },
  );
}

export async function updateWhatsAppAutomation(
  conversationId: string,
  paused: boolean,
  reason?: string,
) {
  return apiClient.post<{ status: string }>(
    `/api/v1/marketing/whatsapp/conversations/${conversationId}/automation`,
    { paused, reason },
  );
}

export async function listWhatsAppTemplates() {
  const response = await apiClient.get<{ items: WhatsAppTemplate[] }>(
    "/api/v1/marketing/whatsapp/templates",
  );
  return response.items;
}

export async function syncWhatsAppTemplates() {
  return apiClient.post<{ synced_count: number; items: WhatsAppTemplate[] }>(
    "/api/v1/marketing/whatsapp/templates/sync",
    {},
  );
}

export async function saveWhatsAppTemplate(template: {
  name: string;
  language_code: string;
  category: string;
  status: string;
  components: Array<Record<string, unknown>>;
}) {
  return apiClient.post<WhatsAppTemplate>("/api/v1/marketing/whatsapp/templates", template);
}

export async function previewWhatsAppCampaign(payload: WhatsAppCampaignPayload) {
  return apiClient.post<WhatsAppCampaignPreview>(
    "/api/v1/marketing/whatsapp/campaigns/preview",
    payload,
  );
}

export async function createWhatsAppCampaign(payload: WhatsAppCampaignPayload) {
  return apiClient.post<WhatsAppCampaign & { preview: WhatsAppCampaignPreview }>(
    "/api/v1/marketing/whatsapp/campaigns",
    payload,
  );
}

export async function listWhatsAppCampaigns() {
  const response = await apiClient.get<{ items: WhatsAppCampaign[] }>(
    "/api/v1/marketing/whatsapp/campaigns",
  );
  return response.items;
}

export async function getWhatsAppCampaign(campaignId: string) {
  return apiClient.get<WhatsAppCampaignDetail>(
    `/api/v1/marketing/whatsapp/campaigns/${campaignId}`,
  );
}

export async function launchWhatsAppCampaign(campaignId: string) {
  return apiClient.post<{ status: string; queued_count: number }>(
    `/api/v1/marketing/whatsapp/campaigns/${campaignId}/launch`,
    { preview_confirmed: true },
  );
}

export async function pauseWhatsAppCampaign(campaignId: string) {
  return apiClient.post<{ status: string }>(
    `/api/v1/marketing/whatsapp/campaigns/${campaignId}/pause`,
    {},
  );
}

export async function cancelWhatsAppCampaign(campaignId: string) {
  return apiClient.post<{ status: string }>(
    `/api/v1/marketing/whatsapp/campaigns/${campaignId}/cancel`,
    {},
  );
}
