/**
 * Backend Payment Service
 *
 * Communicates with FastAPI Backend /api/v1/payments endpoints
 */

import { apiClient } from './api-client';

// Types
export type PaymentStatus = 'pending' | 'payment_submitted' | 'paid' | 'failed' | 'refunded';

export interface CreatePaymentDTO {
  order_id: string;
  amount: number;
  method: 'paynow';
  transaction_id?: string;
  screenshot_url?: string;
  notes?: string;
}

export interface Payment {
  payment_id: string;
  order_id: string;
  amount: number;
  currency?: string;
  method?: string;
  payment_method: string;
  status: PaymentStatus;
  transaction_id?: string;
  screenshot_url?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentFilters {
  status?: PaymentStatus;
  order_id?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Get all payments with optional filtering (admin only)
 */
export async function getPayments(filters?: PaymentFilters): Promise<PaginatedResponse<Payment>> {
  try {
    const response = await apiClient.get<{
      payments?: Payment[];
      total_count?: number;
      page: number;
      page_size: number;
      items?: Payment[];
      total?: number;
    }>('/api/v1/payments', filters);
    const items = (response.items || response.payments || []).map(normalizePayment);
    const total = response.total ?? response.total_count ?? items.length;
    return {
      items,
      total,
      page: response.page,
      page_size: response.page_size,
      total_pages: Math.max(1, Math.ceil(total / response.page_size)),
    };
  } catch (error) {
    console.error('Error fetching payments:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch payments');
  }
}

/**
 * Get single payment by ID (admin only)
 */
export async function getPaymentById(paymentId: string): Promise<Payment> {
  try {
    const payment = await apiClient.get<Payment>(`/api/v1/payments/${paymentId}`);
    return normalizePayment(payment);
  } catch (error) {
    console.error('Error fetching payment:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch payment');
  }
}

/**
 * Update payment status (admin only)
 */
export async function updatePaymentStatus(
  paymentId: string,
  status: PaymentStatus
): Promise<Payment> {
  try {
    const payment = await apiClient.put<Payment>(`/api/v1/payments/${paymentId}`, { status });
    return normalizePayment(payment);
  } catch (error) {
    console.error('Error updating payment status:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to update payment status');
  }
}

/**
 * Create a new payment record (admin only)
 */
export async function createPayment(paymentData: CreatePaymentDTO): Promise<Payment> {
  try {
    const payment = await apiClient.post<Payment>('/api/v1/payments', paymentData);
    return normalizePayment(payment);
  } catch (error) {
    console.error('Error creating payment:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to create payment');
  }
}

function normalizePayment(payment: Payment): Payment {
  return {
    ...payment,
    payment_method: payment.payment_method || payment.method || 'paynow',
  };
}
