import { apiClient } from "@/lib/api-client";

export interface FAQItem {
  keywords: string[];
  response_en: string;
  response_zh: string;
  recommend_product_id?: string | null;
}

export interface ChatbotPackage {
  code: string;
  name_zh: string;
  name_en: string;
  description_zh: string;
  description_en: string;
  price_sgd: number;
  pack_count: number;
  box_count?: number | null;
  target_audience: Array<
    "self_care" | "pregnancy" | "postpartum" | "gift_elder" | "unknown"
  >;
  hero: boolean;
  free_shipping_eligible: boolean;
}

export interface KnowledgeBaseFaq {
  question: string;
  answer: string;
}

export interface KnowledgeBase {
  usps: string[];
  faq: KnowledgeBaseFaq[];
  medical_disclaimer: string;
  logistics: string;
  consumption: string;
  comparisons: string;
}

export interface FollowUpRuleCell {
  instruction: string;
}

export interface ChatbotSettings {
  system_prompt: string;
  handoff_message: string;
  packages: Record<string, ChatbotPackage>;
  knowledge_base: KnowledgeBase;
  crm_follow_up_rules: Record<string, Record<string, FollowUpRuleCell>>;
  payment: {
    paynow: {
      enabled: boolean;
      account_name: string;
      payment_qr_image: string;
      payment_qr_alt: string;
      payment_reference_prefix: string;
      payment_note: string;
    };
  };
  escalation: {
    enabled: boolean;
    private_whatsapp_number: string;
    whatsapp_template_name: string;
    pause_automation_on_handoff: boolean;
  };
  faq: FAQItem[];
}

export async function getChatbotSettings(): Promise<ChatbotSettings> {
  return apiClient.get<ChatbotSettings>("/api/v1/chatbot/settings");
}

export async function updateChatbotSettings(
  settings: Partial<ChatbotSettings>,
): Promise<ChatbotSettings> {
  return apiClient.put<ChatbotSettings>("/api/v1/chatbot/settings", settings);
}
