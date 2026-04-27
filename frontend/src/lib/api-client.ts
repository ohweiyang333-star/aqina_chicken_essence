/**
 * API Client for communicating with FastAPI Backend
 *
 * This client handles:
 * - Automatic authentication token attachment
 * - Type-safe requests/responses
 * - Unified error handling
 * - API base URL configuration
 */

interface ApiClientConfig {
  baseURL: string;
  getAuthToken: () => Promise<string | null>;
}

interface ApiErrorResponse {
  detail: string;
  status_code?: number;
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';
type QueryValue = string | number | boolean | null | undefined;
type QueryParams = object;

export class ApiClient {
  private baseURL: string;
  private getAuthToken: () => Promise<string | null>;

  constructor(config: ApiClientConfig) {
    this.baseURL = config.baseURL.replace(/\/$/, ''); // Remove trailing slash
    this.getAuthToken = config.getAuthToken;
  }

  /**
   * Get authentication headers for requests
   */
  private async getAuthHeaders(): Promise<HeadersInit> {
    const token = await this.getAuthToken();
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  /**
   * Build full URL for API endpoint
   */
  private buildUrl(endpoint: string, params?: QueryParams): string {
    const url = new URL(`${this.baseURL}${endpoint}`);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (isQueryValue(value) && value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    return url.toString();
  }

  /**
   * Make HTTP request with error handling
   */
  private async request<T>(
    method: HttpMethod,
    endpoint: string,
    data?: object,
    params?: QueryParams
  ): Promise<T> {
    const url = this.buildUrl(endpoint, params);
    const headers = await this.getAuthHeaders();

    const config: RequestInit = {
      method,
      headers,
    };

    if (data && method !== 'GET') {
      config.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, config);

      // Handle non-OK responses
      if (!response.ok) {
        const errorData: ApiErrorResponse = await response.json().catch(() => ({
          detail: 'Unknown error occurred',
        }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Re-throw with more context
      if (error instanceof Error) {
        throw new Error(`API request failed: ${error.message}`);
      }
      throw new Error('Unknown API error');
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, params?: QueryParams): Promise<T> {
    return this.request<T>('GET', endpoint, undefined, params);
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data: object): Promise<T> {
    return this.request<T>('POST', endpoint, data);
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data: object): Promise<T> {
    return this.request<T>('PUT', endpoint, data);
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>('DELETE', endpoint);
  }
}

function isQueryValue(value: unknown): value is QueryValue {
  const valueType = typeof value;
  return (
    value === null ||
    value === undefined ||
    valueType === 'string' ||
    valueType === 'number' ||
    valueType === 'boolean'
  );
}

/**
 * Create singleton API client instance
 */
export function createApiClient(): ApiClient {
  const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Get Firebase ID token for authentication
  const getAuthToken = async (): Promise<string | null> => {
    try {
      // Dynamically import firebase/auth to avoid SSR issues
      if (typeof window === 'undefined') return null;

      const { auth } = await import('@/lib/firebase');

      const user = auth.currentUser;
      if (!user) return null;

      return await user.getIdToken();
    } catch (error) {
      console.error('Error getting auth token:', error);
      return null;
    }
  };

  return new ApiClient({ baseURL, getAuthToken });
}

// Export singleton instance
export const apiClient = createApiClient();
