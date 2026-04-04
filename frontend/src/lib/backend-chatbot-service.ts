/**
 * Backend Chatbot Service
 *
 * Communicates with FastAPI Backend /api/v1/chatbot endpoints
 */

import { apiClient } from './api-client';

// Types
export interface ChatbotSettings {
  faq: Array<{
    question: string;
    answer: string;
    order?: number;
  }>;
  cart_abandonment_message?: string;
  restock_reminder_enabled?: boolean;
  restock_reminder_message?: string;
  updated_at: string;
}

/**
 * Get chatbot settings (public endpoint)
 */
export async function getChatbotSettings(): Promise<ChatbotSettings> {
  try {
    const settings = await apiClient.get<ChatbotSettings>('/api/v1/chatbot/settings');
    return settings;
  } catch (error) {
    console.error('Error fetching chatbot settings:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch chatbot settings');
  }
}

/**
 * Update chatbot settings (admin only)
 */
export async function updateChatbotSettings(settings: Partial<ChatbotSettings>): Promise<ChatbotSettings> {
  try {
    const updated = await apiClient.put<ChatbotSettings>('/api/v1/chatbot/settings', settings);
    return updated;
  } catch (error) {
    console.error('Error updating chatbot settings:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to update chatbot settings');
  }
}
