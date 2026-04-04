/**
 * Backend Customer Service
 *
 * Communicates with FastAPI Backend /api/v1/customers endpoints
 */

import { apiClient } from './api-client';

// Types
export interface Customer {
  customer_id: string;
  name: string;
  email: string;
  phone: string;
  address?: string;
  total_orders: number;
  total_spent: number;
  created_at: string;
  updated_at: string;
}

export interface CustomerFilters {
  page?: number;
  page_size?: number;
  min_orders?: number;
  min_spent?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Get all customers with optional filtering (admin only)
 */
export async function getCustomers(filters?: CustomerFilters): Promise<PaginatedResponse<Customer>> {
  try {
    const response = await apiClient.get<PaginatedResponse<Customer>>('/api/v1/customers', filters);
    return response;
  } catch (error) {
    console.error('Error fetching customers:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch customers');
  }
}

/**
 * Get single customer by ID (admin only)
 */
export async function getCustomerById(customerId: string): Promise<Customer> {
  try {
    const customer = await apiClient.get<Customer>(`/api/v1/customers/${customerId}`);
    return customer;
  } catch (error) {
    console.error('Error fetching customer:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch customer');
  }
}

/**
 * Update customer information (admin only)
 */
export async function updateCustomer(
  customerId: string,
  updates: Partial<Omit<Customer, 'customer_id' | 'total_orders' | 'total_spent' | 'created_at' | 'updated_at'>>
): Promise<Customer> {
  try {
    const customer = await apiClient.put<Customer>(`/api/v1/customers/${customerId}`, updates);
    return customer;
  } catch (error) {
    console.error('Error updating customer:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to update customer');
  }
}

/**
 * Delete a customer (admin only)
 */
export async function deleteCustomer(customerId: string): Promise<void> {
  try {
    await apiClient.delete<void>(`/api/v1/customers/${customerId}`);
  } catch (error) {
    console.error('Error deleting customer:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to delete customer');
  }
}
