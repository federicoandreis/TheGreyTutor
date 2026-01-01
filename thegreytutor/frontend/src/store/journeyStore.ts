/**
 * Journey Store - Context-based state management for Journey/Map feature
 *
 * Manages the user's journey state, region unlocks, and progression.
 */

import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import {
  getJourneyState as fetchJourneyState,
  travelToRegion as apiTravelToRegion,
  updateQuizCompletion,
  JourneyState,
  RegionProgress,
} from '../services/api/journey';

// Type aliases for backward compatibility
type RegionStatus = RegionProgress;
type Achievement = string; // Achievements are now just strings (badge IDs)

interface TravelResponse {
  success: boolean;
  message?: string;
  region_data?: any;
}

interface QuizCompletionResponse {
  knowledge_points_earned: number;
  achievements_earned: Achievement[];
  regions_unlocked: string[];
}

// ============================================================================
// State Interface
// ============================================================================

interface JourneyStoreState {
  // Journey data
  journeyState: JourneyState | null;
  currentRegionData: TravelResponse['region_data'] | null;

  // UI state
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;

  // Notifications for user feedback
  notifications: {
    knowledgePointsEarned?: number;
    achievementsEarned?: Achievement[];
    regionsUnlocked?: string[];
  };
}

// ============================================================================
// Actions
// ============================================================================

type JourneyAction =
  | { type: 'SET_JOURNEY_STATE'; payload: JourneyState }
  | { type: 'SET_CURRENT_REGION_DATA'; payload: TravelResponse['region_data'] | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_INITIALIZED'; payload: boolean }
  | {
      type: 'SET_QUIZ_COMPLETION_NOTIFICATIONS';
      payload: {
        knowledgePointsEarned: number;
        achievementsEarned: Achievement[];
        regionsUnlocked: string[];
      };
    }
  | { type: 'CLEAR_NOTIFICATIONS' }
  | { type: 'RESET_JOURNEY_STATE' };

// ============================================================================
// Initial State
// ============================================================================

const initialState: JourneyStoreState = {
  journeyState: null,
  currentRegionData: null,
  isLoading: false,
  isInitialized: false,
  error: null,
  notifications: {},
};

// ============================================================================
// Reducer
// ============================================================================

function journeyReducer(state: JourneyStoreState, action: JourneyAction): JourneyStoreState {
  switch (action.type) {
    case 'SET_JOURNEY_STATE':
      return {
        ...state,
        journeyState: action.payload,
        error: null,
      };

    case 'SET_CURRENT_REGION_DATA':
      return {
        ...state,
        currentRegionData: action.payload,
      };

    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };

    case 'SET_INITIALIZED':
      return {
        ...state,
        isInitialized: action.payload,
      };

    case 'SET_QUIZ_COMPLETION_NOTIFICATIONS':
      return {
        ...state,
        notifications: {
          knowledgePointsEarned: action.payload.knowledgePointsEarned,
          achievementsEarned: action.payload.achievementsEarned,
          regionsUnlocked: action.payload.regionsUnlocked,
        },
      };

    case 'CLEAR_NOTIFICATIONS':
      return {
        ...state,
        notifications: {},
      };

    case 'RESET_JOURNEY_STATE':
      return initialState;

    default:
      return state;
  }
}

// ============================================================================
// Context
// ============================================================================

const JourneyContext = createContext<{
  state: JourneyStoreState;
  dispatch: React.Dispatch<JourneyAction>;
} | null>(null);

// ============================================================================
// Provider
// ============================================================================

export function JourneyProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(journeyReducer, initialState);

  return React.createElement(JourneyContext.Provider, { value: { state, dispatch } }, children);
}

// ============================================================================
// Hook
// ============================================================================

export function useJourneyStore() {
  const context = useContext(JourneyContext);
  if (!context) {
    throw new Error('useJourneyStore must be used within JourneyProvider');
  }
  return context;
}

// ============================================================================
// Action Creators / Thunks
// ============================================================================

/**
 * Initialize journey state by fetching from API.
 */
export async function initializeJourney(
  dispatch: React.Dispatch<JourneyAction>
): Promise<boolean> {
  try {
    dispatch({ type: 'SET_LOADING', payload: true });

    const journeyState = await fetchJourneyState();

    dispatch({ type: 'SET_JOURNEY_STATE', payload: journeyState });
    dispatch({ type: 'SET_INITIALIZED', payload: true });
    dispatch({ type: 'SET_LOADING', payload: false });

    return true;
  } catch (error: any) {
    console.error('Failed to initialize journey:', error);
    dispatch({ type: 'SET_ERROR', payload: error.message || 'Failed to load journey data' });
    dispatch({ type: 'SET_LOADING', payload: false });
    return false;
  }
}

/**
 * Refresh journey state from API.
 */
export async function refreshJourneyState(dispatch: React.Dispatch<JourneyAction>): Promise<void> {
  try {
    dispatch({ type: 'SET_LOADING', payload: true });

    const journeyState = await fetchJourneyState();

    dispatch({ type: 'SET_JOURNEY_STATE', payload: journeyState });
    dispatch({ type: 'SET_LOADING', payload: false });
  } catch (error: any) {
    console.error('Failed to refresh journey state:', error);
    dispatch({ type: 'SET_ERROR', payload: error.message || 'Failed to refresh journey data' });
  }
}

/**
 * Travel to a region.
 *
 * @param regionName - Name of the region to travel to
 * @returns Travel response with success status and message
 */
export async function travelToRegion(
  dispatch: React.Dispatch<JourneyAction>,
  regionName: string
): Promise<TravelResponse> {
  try {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    // Call new API and get updated state back
    const updatedState = await apiTravelToRegion(regionName);
    
    // Update the entire journey state
    dispatch({ type: 'SET_JOURNEY_STATE', payload: updatedState });
    dispatch({ type: 'SET_LOADING', payload: false });
    
    return {
      success: true,
      message: `Traveled to ${regionName}`,
    };
  } catch (error: any) {
    console.error('Failed to travel to region:', error);
    dispatch({ type: 'SET_ERROR', payload: error.message || 'Failed to travel to region' });
    dispatch({ type: 'SET_LOADING', payload: false });

    return {
      success: false,
      message: error.message || 'An error occurred while traveling',
    };
  }
}

/**
 * Record quiz completion.
 *
 * @param params - Quiz completion parameters
 * @returns Quiz completion response with rewards
 */
export async function completeQuiz(
  dispatch: React.Dispatch<JourneyAction>,
  params: {
    region: string;
    points_earned: number;
    quiz_id: string;
  }
): Promise<QuizCompletionResponse | null> {
  try {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    // Call new API
    const updatedState = await updateQuizCompletion(params);
    
    // Mock response for notifications (adapt based on what backend returns)
    const response: QuizCompletionResponse = {
      knowledge_points_earned: params.points_earned,
      achievements_earned: [],
      regions_unlocked: [],
    };

    // Set notifications for user feedback
    dispatch({
      type: 'SET_QUIZ_COMPLETION_NOTIFICATIONS',
      payload: {
        knowledgePointsEarned: response.knowledge_points_earned,
        achievementsEarned: response.achievements_earned,
        regionsUnlocked: response.regions_unlocked,
      },
    });

    // Update journey state
    dispatch({ type: 'SET_JOURNEY_STATE', payload: updatedState });
    dispatch({ type: 'SET_LOADING', payload: false });
    
    return response;
  } catch (error: any) {
    console.error('Failed to complete quiz:', error);
    dispatch({ type: 'SET_ERROR', payload: error.message || 'Failed to record quiz completion' });
    dispatch({ type: 'SET_LOADING', payload: false });
    return null;
  }
}

/**
 * Clear notifications after user has seen them.
 */
export function clearNotifications(dispatch: React.Dispatch<JourneyAction>): void {
  dispatch({ type: 'CLEAR_NOTIFICATIONS' });
}

/**
 * Reset journey state (e.g., on logout).
 */
export function resetJourneyState(dispatch: React.Dispatch<JourneyAction>): void {
  dispatch({ type: 'RESET_JOURNEY_STATE' });
}

// ============================================================================
// Selectors (Helper functions to extract data from state)
// ============================================================================

/**
 * Get the current region status.
 */
export function getCurrentRegionStatus(state: JourneyStoreState): RegionStatus | null {
  if (!state.journeyState || !state.journeyState.current_region) {
    return null;
  }

  return (
    state.journeyState.journey_progress?.find(
      (region: RegionProgress) => region.region_name === state.journeyState!.current_region
    ) || null
  );
}

/**
 * Get all unlocked regions.
 */
export function getUnlockedRegions(state: JourneyStoreState): RegionStatus[] {
  if (!state.journeyState) {
    return [];
  }

  return state.journeyState.journey_progress?.filter((region: RegionProgress) => region.is_unlocked) || [];
}

/**
 * Get all locked but unlockable regions.
 */
export function getUnlockableRegions(state: JourneyStoreState): RegionStatus[] {
  if (!state.journeyState) {
    return [];
  }

  // Unlockable means adjacent to unlocked regions (would need backend logic)
  // For now, return empty array
  return [];
}

/**
 * Get all completed regions.
 */
export function getCompletedRegions(state: JourneyStoreState): RegionStatus[] {
  if (!state.journeyState) {
    return [];
  }

  return state.journeyState.journey_progress?.filter((region: RegionProgress) => region.is_completed) || [];
}

/**
 * Get user's total knowledge points.
 */
export function getKnowledgePoints(state: JourneyStoreState): number {
  return state.journeyState?.total_knowledge_points || 0;
}

/**
 * Get user's earned achievements.
 */
export function getEarnedAchievements(state: JourneyStoreState): Achievement[] {
  return state.journeyState?.achievement_badges || [];
}

/**
 * Check if a specific region is unlocked.
 */
export function isRegionUnlocked(state: JourneyStoreState, regionName: string): boolean {
  return state.journeyState?.unlocked_regions?.includes(regionName) || false;
}
