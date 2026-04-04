/**
 * Backend Order Service
 *
 * Communicates with FastAPI Backend /api/v1/orders endpoints
 * Replaces direct Firebase SDK calls
 */

import { apiClient } from './api-client';

// Types based on Backend API models
export type OrderStatus = 'pending' | 'confirmed' | 'preparing' | 'shipped' | 'delivered' | 'cancelled';

export interface OrderItem {
  product_id: string;
  product_name: string;
  quantity: number;
  price: number;
}

export interface CreateOrderDTO {
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  customer_address: string;
  items: OrderItem[];
  total_amount: number;
  currency: string;
  notes?: string;
}

export interface Order {
  order_id: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  customer_address: string;
  items: OrderItem[];
  total_amount: number;
  currency: string;
  status: OrderStatus;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface OrderFilters {
  status?: OrderStatus;
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
 * Create a new order (public endpoint, no auth required)
 */
export async function createOrder(orderData: CreateOrderDTO): Promise<Order> {
  try {
    const order = await apiClient.post<Order>('/api/v1/orders', orderData);
    return order;
  } catch (error) {
    console.error('Error creating order:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to create order');
  }
}

/**
 * Get all orders with optional filtering (admin only, requires auth)
 */
export async function getOrders(filters?: OrderFilters): Promise<PaginatedResponse<Order>> {
  try {
    const response = await apiClient.get<PaginatedResponse<Order>>('/api/v1/orders', filters);
    return response;
  } catch (error) {
    console.error('Error fetching orders:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch orders');
  }
}

/**
 * Get single order by ID (admin only)
 */
export async function getOrderById(orderId: string): Promise<Order> {
  try {
    const order = await apiClient.get<Order>(`/api/v1/orders/${orderId}`);
    return order;
  } catch (error) {
    console.error('Error fetching order:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch order');
  }
}

/**
 * Update order status (admin only)
 */
export async function updateOrderStatus(orderId: string, status: OrderStatus): Promise<Order> {
  try {
    const order = await apiClient.put<Order>(`/api/v1/orders/${orderId}`, { status });
    return order;
  } catch (error) {
    console.error('Error updating order status:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to update order status');
  }
}
