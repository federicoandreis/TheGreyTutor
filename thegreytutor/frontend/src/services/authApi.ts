/**
 * Authentication API Service
 * 
 * Handles all authentication-related API calls to the backend.
 * Replaces mock authentication with real API endpoints.
 */

import * as SecureStore from 'expo-secure-store';

// Use computer's IP for mobile device access (localhost doesn't work from phone)
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://192.168.0.225:8000';

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

// Types
export interface AuthUser {
  id: string;
  username: string;
  email: string;
  name: string | null;
  role: string;
  created_at: string;
  last_login: string | null;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  refresh_expires_at: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user: AuthUser;
  tokens: AuthTokens;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

class AuthApiService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  /**
   * Initialize the auth service by loading tokens from secure storage
   */
  async initialize(): Promise<boolean> {
    try {
      this.accessToken = await SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
      this.refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
      return !!this.accessToken;
    } catch (error) {
      console.error('Failed to load tokens from storage:', error);
      return false;
    }
  }

  /**
   * Store tokens securely
   */
  private async storeTokens(tokens: AuthTokens): Promise<void> {
    try {
      await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, tokens.access_token);
      await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, tokens.refresh_token);
      this.accessToken = tokens.access_token;
      this.refreshToken = tokens.refresh_token;
    } catch (error) {
      console.error('Failed to store tokens:', error);
      throw new Error('Failed to save authentication data');
    }
  }

  /**
   * Clear stored tokens
   */
  private async clearTokens(): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
      await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
      this.accessToken = null;
      this.refreshToken = null;
    } catch (error) {
      console.error('Failed to clear tokens:', error);
    }
  }

  /**
   * Get current access token
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  /**
   * Make an authenticated API request
   */
  async authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
    if (!this.accessToken) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    // If token expired, try to refresh
    if (response.status === 401 && this.refreshToken) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        // Retry the request with new token
        return fetch(url, {
          ...options,
          headers: {
            ...options.headers,
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json',
          },
        });
      }
    }

    return response;
  }

  /**
   * Register a new user
   */
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
      const message = typeof error.detail === 'string' 
        ? error.detail 
        : (error.message || JSON.stringify(error.detail) || 'Registration failed');
      throw new Error(message);
    }

    const result: AuthResponse = await response.json();
    await this.storeTokens(result.tokens);
    return result;
  }

  /**
   * Login an existing user
   */
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      const message = typeof error.detail === 'string' 
        ? error.detail 
        : (error.message || JSON.stringify(error.detail) || 'Invalid email or password');
      throw new Error(message);
    }

    const result: AuthResponse = await response.json();
    await this.storeTokens(result.tokens);
    return result;
  }

  /**
   * Refresh the access token
   */
  async refreshAccessToken(): Promise<boolean> {
    if (!this.refreshToken) {
      return false;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });

      if (!response.ok) {
        await this.clearTokens();
        return false;
      }

      const tokens: AuthTokens = await response.json();
      await this.storeTokens(tokens);
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      await this.clearTokens();
      return false;
    }
  }

  /**
   * Logout the current user
   */
  async logout(): Promise<void> {
    try {
      if (this.accessToken) {
        await this.authenticatedFetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          body: JSON.stringify({ refresh_token: this.refreshToken }),
        });
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      await this.clearTokens();
    }
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<AuthUser> {
    const response = await this.authenticatedFetch(`${API_BASE_URL}/auth/me`);

    if (!response.ok) {
      throw new Error('Failed to get user profile');
    }

    return response.json();
  }

  /**
   * Change password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    const response = await this.authenticatedFetch(`${API_BASE_URL}/auth/me/password`, {
      method: 'PUT',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Password change failed' }));
      throw new Error(error.detail || 'Failed to change password');
    }
  }
}

// Export singleton instance
export const authApi = new AuthApiService();
