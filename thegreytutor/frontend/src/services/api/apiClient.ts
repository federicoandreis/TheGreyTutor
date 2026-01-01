/**
 * Centralized API Client using Axios
 * 
 * Provides a single configured axios instance with:
 * - Request interceptors for authentication
 * - Response interceptors for error handling
 * - Retry logic for failed requests
 * - Consistent error formatting
 */

import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import * as SecureStore from 'expo-secure-store';
import { config } from '../../utils/config';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public originalError?: AxiosError
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Create and configure the axios instance
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: config.apiUrl,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  /**
   * Request interceptor - Add JWT token to headers
   */
  client.interceptors.request.use(
    async (requestConfig: InternalAxiosRequestConfig) => {
      try {
        // Retrieve JWT token from secure storage
        const token = await SecureStore.getItemAsync('jwt_token');
        
        if (token && requestConfig.headers) {
          requestConfig.headers.Authorization = `Bearer ${token}`;
        }
        
        // Log requests if enabled in global config
        if (config.enableLogging) {
          console.log(`[API Request] ${requestConfig.method?.toUpperCase()} ${requestConfig.url}`);
        }
        
        return requestConfig;
      } catch (error) {
        console.error('[API Client] Error in request interceptor:', error);
        return requestConfig;
      }
    },
    (error) => {
      console.error('[API Client] Request interceptor error:', error);
      return Promise.reject(error);
    }
  );

  /**
   * Response interceptor - Handle errors and token refresh
   */
  client.interceptors.response.use(
    (response) => {
      if (config.enableLogging) {
        console.log(`[API Response] ${response.status} ${response.config.url}`);
      }
      return response;
    },
    async (error: AxiosError) => {
      const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

      // Handle 401 Unauthorized - Token expired
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        
        try {
          // TODO: Implement token refresh logic
          // const newToken = await refreshToken();
          // await SecureStore.setItemAsync('jwt_token', newToken);
          // originalRequest.headers.Authorization = `Bearer ${newToken}`;
          // return client(originalRequest);
          
          // For now, just clear the token and throw error
          await SecureStore.deleteItemAsync('jwt_token');
          throw new ApiError('Session expired. Please login again.', 401, error);
        } catch (refreshError) {
          console.error('[API Client] Token refresh failed:', refreshError);
          throw new ApiError('Authentication failed', 401, error);
        }
      }

      // Handle network errors
      if (error.message === 'Network Error' || !error.response) {
        throw new ApiError(
          'Network error. Please check your connection and try again.',
          undefined,
          error
        );
      }

      // Handle timeout
      if (error.code === 'ECONNABORTED') {
        throw new ApiError(
          'Request timeout. The server took too long to respond.',
          undefined,
          error
        );
      }

      // Handle other HTTP errors
      const statusCode = error.response?.status;
      const errorData = error.response?.data as any;
      const message = errorData?.detail || 
                     errorData?.message || 
                     'An unexpected error occurred';

      console.error(`[API Client] Error ${statusCode}:`, message);
      throw new ApiError(message, statusCode, error);
    }
  );

  return client;
};

/**
 * Singleton API client instance
 */
export const apiClient = createApiClient();

/**
 * Helper function for making GET requests
 */
export const get = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return apiClient.get<T>(url, config).then(response => response.data);
};

/**
 * Helper function for making POST requests
 */
export const post = <T = any>(
  url: string, 
  data?: any, 
  config?: AxiosRequestConfig
): Promise<T> => {
  return apiClient.post<T>(url, data, config).then(response => response.data);
};

/**
 * Helper function for making PUT requests
 */
export const put = <T = any>(
  url: string, 
  data?: any, 
  config?: AxiosRequestConfig
): Promise<T> => {
  return apiClient.put<T>(url, data, config).then(response => response.data);
};

/**
 * Helper function for making DELETE requests
 */
export const del = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return apiClient.delete<T>(url, config).then(response => response.data);
};

/**
 * Check if error is an ApiError
 */
export const isApiError = (error: any): error is ApiError => {
  return error instanceof ApiError;
};
