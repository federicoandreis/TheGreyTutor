/**
 * Journey API Client
 *
 * Provides methods to interact with the Journey Agent backend API.
 */

import { authApi } from './authApi';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

export interface RegionStatus {
  name: string;
  display_name: string;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  is_unlocked: boolean;
  can_unlock: boolean;
  unlock_requirements: {
    knowledge_points: boolean;
    prerequisite_regions: boolean;
    mastered_themes: boolean;
  };
  completion_percentage: number;
  visit_count: number;
  is_completed: boolean;
  map_coordinates: {
    x: number;
    y: number;
    radius: number;
  };
}

export interface JourneyPath {
  name: string;
  display_name: string;
  description: string;
  ordered_regions: string[];
  narrative_theme: string;
  estimated_duration_hours: number;
  path_color: string;
}

export interface Achievement {
  code: string;
  name: string;
  description: string;
  category: 'region' | 'quiz' | 'knowledge' | 'special';
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  icon_name?: string;
  badge_color?: string;
  is_earned?: boolean;
  earned_at?: string;
}

export interface JourneyState {
  current_region: string | null;
  current_path: string | null;
  knowledge_points: number;
  unlocked_regions: string[];
  active_paths: string[];
  achievement_badges: Achievement[];
  mastered_communities: string[];
  total_regions_completed: number;
  total_quizzes_taken: number;
  journey_started_at: string | null;
  last_activity: string | null;
  region_statuses: RegionStatus[];
  available_paths: JourneyPath[];
}

export interface TravelResponse {
  success: boolean;
  message: string;
  region_data?: {
    name: string;
    display_name: string;
    description: string;
    difficulty_level: string;
    lore_depth: string;
    available_quiz_themes: string[];
    lore_snippets: Array<{
      concept: string;
      description: string;
    }>;
    visit_count: number;
    completion_percentage: number;
  };
}

export interface QuizCompletionResponse {
  knowledge_points_earned: number;
  new_completion_percentage: number;
  achievements_earned: Achievement[];
  regions_unlocked: string[];
}

export interface RegionDetail {
  name: string;
  display_name: string;
  description: string;
  difficulty_level: string;
  map_coordinates: {
    x: number;
    y: number;
    radius: number;
  };
  prerequisite_regions: string[];
  knowledge_points_required: number;
  available_quiz_themes: string[];
  is_unlocked: boolean;
  can_unlock: boolean;
  completion_percentage: number;
}

export interface Region {
  name: string;
  display_name: string;
  difficulty_level: string;
  map_coordinates: {
    x: number;
    y: number;
    radius: number;
  };
  is_unlocked: boolean;
  knowledge_points_required: number;
}

// ============================================================================
// API Client
// ============================================================================

class JourneyApiClient {
  /**
   * Get the complete journey state for the current user.
   */
  async getJourneyState(): Promise<JourneyState> {
    const response = await authApi.authenticatedFetch(`${API_URL}/api/journey/state`);
    if (!response.ok) {
      throw new Error(`Failed to get journey state: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * Attempt to travel to a region.
   *
   * @param regionName - Name of the region to travel to
   * @returns Travel response with success status and Gandalf's narration
   */
  async travelToRegion(regionName: string): Promise<TravelResponse> {
    const response = await authApi.authenticatedFetch(`${API_URL}/api/journey/travel`, {
      method: 'POST',
      body: JSON.stringify({ region_name: regionName }),
    });
    if (!response.ok) {
      throw new Error(`Failed to travel to region: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * Record quiz completion in a region.
   *
   * @param params - Quiz completion parameters
   * @returns Knowledge points earned, achievements, and newly unlocked regions
   */
  async completeQuiz(params: {
    region_name: string;
    quiz_id: string;
    score: number;
    questions_answered: number;
    answers: Array<{
      question_id?: string;
      concepts?: string[];
      [key: string]: any;
    }>;
  }): Promise<QuizCompletionResponse> {
    const response = await authApi.authenticatedFetch(`${API_URL}/api/journey/complete-quiz`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
    if (!response.ok) {
      throw new Error(`Failed to complete quiz: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * Get detailed information about a specific region.
   *
   * @param regionName - Name of the region
   * @returns Detailed region information
   */
  async getRegionDetails(regionName: string): Promise<RegionDetail> {
    const response = await authApi.authenticatedFetch(`${API_URL}/api/journey/regions/${regionName}`);
    if (!response.ok) {
      throw new Error(`Failed to get region details: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * Get list of all available regions.
   *
   * @returns Array of all regions with basic info and unlock status
   */
  async listRegions(): Promise<Region[]> {
    const response = await authApi.authenticatedFetch(`${API_URL}/api/journey/regions`);
    if (!response.ok) {
      throw new Error(`Failed to list regions: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * Get list of all available journey paths.
   *
   * @returns Array of journey paths
   */
  async listPaths(): Promise<JourneyPath[]> {
    const response = await authApi.authenticatedFetch(`${API_URL}/api/journey/paths`);
    if (!response.ok) {
      throw new Error(`Failed to list paths: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * Get list of all achievements with earned status.
   *
   * @returns Array of achievements
   */
  async listAchievements(): Promise<Achievement[]> {
    const response = await authApi.authenticatedFetch(`${API_URL}/api/journey/achievements`);
    if (!response.ok) {
      throw new Error(`Failed to list achievements: ${response.statusText}`);
    }
    return await response.json();
  }
}

export const journeyApi = new JourneyApiClient();
