/**
 * Authentication API endpoints
 * 
 * Handles user registration, login, and token management
 */

import { post } from './apiClient';
import * as SecureStore from 'expo-secure-store';

/**
 * API Types
 */
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  username: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    username: string;
  };
}

/**
 * Login user and store JWT token
 */
export const login = async (credentials: LoginRequest): Promise<AuthResponse> => {
  const response = await post<AuthResponse>('/auth/login', credentials);
  
  // Store token securely
  await SecureStore.setItemAsync('jwt_token', response.access_token);
  
  return response;
};

/**
 * Register new user and store JWT token
 */
export const register = async (userData: RegisterRequest): Promise<AuthResponse> => {
  const response = await post<AuthResponse>('/auth/register', userData);
  
  // Store token securely
  await SecureStore.setItemAsync('jwt_token', response.access_token);
  
  return response;
};

/**
 * Logout user and clear stored token
 */
export const logout = async (): Promise<void> => {
  try {
    // Optional: Call backend logout endpoint if it exists
    // await post('/auth/logout');
    
    // Clear stored token
    await SecureStore.deleteItemAsync('jwt_token');
  } catch (error) {
    console.error('[Auth API] Logout error:', error);
    // Still clear token even if API call fails
    await SecureStore.deleteItemAsync('jwt_token');
  }
};

/**
 * Check if user is authenticated by verifying token exists
 */
export const isAuthenticated = async (): Promise<boolean> => {
  try {
    const token = await SecureStore.getItemAsync('jwt_token');
    return !!token;
  } catch (error) {
    console.error('[Auth API] isAuthenticated error:', error);
    return false;
  }
};

/**
 * Get current user profile
 */
export const getCurrentUser = async () => {
  // TODO: Implement when backend endpoint is available
  // return get('/auth/me');
  throw new Error('Not implemented');
};
