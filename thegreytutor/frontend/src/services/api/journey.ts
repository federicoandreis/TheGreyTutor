/**
 * Journey API endpoints
 * 
 * Handles journey state, region navigation, and progress tracking
 */

import { get, post } from './apiClient';

/**
 * API Types
 */
export interface JourneyState {
  user_id: string;
  current_region: string;
  total_knowledge_points: number;
  unlocked_regions: string[];
  completed_regions: string[];
  achievement_badges: string[];
  journey_progress: RegionProgress[];
}

export interface RegionProgress {
  region_name: string;
  knowledge_points: number;
  quizzes_completed: number;
  is_unlocked: boolean;
  is_completed: boolean;
}

export interface TravelRequest {
  region: string;
}

export interface QuizCompletionRequest {
  region: string;
  points_earned: number;
  quiz_id: string;
}

/**
 * Get user's current journey state
 */
export const getJourneyState = async (): Promise<JourneyState> => {
  return get<JourneyState>('/api/journey/state');
};

/**
 * Travel to a new region
 */
export const travelToRegion = async (regionName: string): Promise<JourneyState> => {
  return post<JourneyState>('/api/journey/travel', { region: regionName });
};

/**
 * Update progress after completing a quiz
 */
export const updateQuizCompletion = async (
  data: QuizCompletionRequest
): Promise<JourneyState> => {
  return post<JourneyState>('/api/journey/quiz-completion', data);
};

/**
 * Get recommended next regions based on user progress
 */
export const getRecommendedRegions = async (): Promise<string[]> => {
  // TODO: Implement when backend endpoint is available
  return get<string[]>('/api/journey/recommend');
};
