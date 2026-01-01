/**
 * Chat API endpoints
 * 
 * Handles conversations with Gandalf AI
 */

import { post } from './apiClient';

/**
 * API Types
 */
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  context?: string;
  region?: string;
}

export interface ChatResponse {
  message: string;
  agent_used?: string;
  context?: any;
}

/**
 * Send a message to Gandalf and get a response
 */
export const sendMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  return post<ChatResponse>('/chat', request);
};

/**
 * Start a new chat conversation
 */
export const startConversation = async (region?: string): Promise<ChatResponse> => {
  return post<ChatResponse>('/chat/start', { region });
};
