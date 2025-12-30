import { journeyApi } from '../../src/services/journeyApi';
import * as authApi from '../../src/services/authApi';

// Mock authApi
jest.mock('../../src/services/authApi', () => ({
  authenticatedFetch: jest.fn(),
}));

describe('JourneyApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getJourneyState', () => {
    it('fetches journey state successfully', async () => {
      const mockJourneyState = {
        current_region: 'shire',
        current_path: 'fellowship',
        knowledge_points: 150,
        unlocked_regions: ['shire', 'bree'],
        active_paths: ['fellowship'],
        achievement_badges: [],
        mastered_communities: [],
        total_regions_completed: 1,
        total_quizzes_taken: 5,
        journey_started_at: '2025-01-01T00:00:00Z',
        last_activity: '2025-01-02T00:00:00Z',
        region_statuses: [],
        available_paths: [],
      };

      (authApi.authenticatedFetch as jest.Mock).mockResolvedValue(mockJourneyState);

      const result = await journeyApi.getJourneyState();

      expect(authApi.authenticatedFetch).toHaveBeenCalledWith('/api/journey/state', {
        method: 'GET',
      });
      expect(result).toEqual(mockJourneyState);
    });

    it('throws error when fetch fails', async () => {
      (authApi.authenticatedFetch as jest.Mock).mockRejectedValue(
        new Error('Network error')
      );

      await expect(journeyApi.getJourneyState()).rejects.toThrow('Network error');
    });
  });

  describe('travelToRegion', () => {
    it('travels to region successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Welcome to Bree!',
        region_data: {
          name: 'bree',
          display_name: 'Bree',
        },
      };

      (authApi.authenticatedFetch as jest.Mock).mockResolvedValue(mockResponse);

      const result = await journeyApi.travelToRegion('bree');

      expect(authApi.authenticatedFetch).toHaveBeenCalledWith('/api/journey/travel', {
        method: 'POST',
        body: JSON.stringify({ region_name: 'bree' }),
      });
      expect(result).toEqual(mockResponse);
    });

    it('handles travel failure', async () => {
      const mockResponse = {
        success: false,
        message: 'Region is locked',
        region_data: null,
      };

      (authApi.authenticatedFetch as jest.Mock).mockResolvedValue(mockResponse);

      const result = await journeyApi.travelToRegion('rivendell');

      expect(result.success).toBe(false);
      expect(result.message).toBe('Region is locked');
    });
  });

  describe('completeQuiz', () => {
    it('completes quiz successfully', async () => {
      const mockResponse = {
        knowledge_points_earned: 50,
        new_completion_percentage: 75,
        achievements_earned: [],
        regions_unlocked: [],
      };

      (authApi.authenticatedFetch as jest.Mock).mockResolvedValue(mockResponse);

      const quizData = {
        region_name: 'shire',
        quiz_id: 'quiz-123',
        score: 0.8,
        questions_answered: 10,
        answers: [],
      };

      const result = await journeyApi.completeQuiz(quizData);

      expect(authApi.authenticatedFetch).toHaveBeenCalledWith(
        '/api/journey/complete-quiz',
        {
          method: 'POST',
          body: JSON.stringify(quizData),
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('handles quiz completion with achievements', async () => {
      const mockResponse = {
        knowledge_points_earned: 100,
        new_completion_percentage: 100,
        achievements_earned: [
          {
            code: 'shire_master',
            name: 'Shire Master',
          },
        ],
        regions_unlocked: ['bree'],
      };

      (authApi.authenticatedFetch as jest.Mock).mockResolvedValue(mockResponse);

      const quizData = {
        region_name: 'shire',
        quiz_id: 'quiz-final',
        score: 1.0,
        questions_answered: 15,
        answers: [],
      };

      const result = await journeyApi.completeQuiz(quizData);

      expect(result.achievements_earned).toHaveLength(1);
      expect(result.regions_unlocked).toContain('bree');
    });
  });

  describe('getRegionDetails', () => {
    it('fetches region details successfully', async () => {
      const mockRegionDetail = {
        name: 'shire',
        display_name: 'The Shire',
        description: 'A peaceful region',
        difficulty_level: 'beginner' as const,
        map_coordinates: { x: 100, y: 150, radius: 20 },
        prerequisite_regions: [],
        knowledge_points_required: 0,
        available_quiz_themes: ['hobbits', 'farming'],
        is_unlocked: true,
        can_unlock: true,
        completion_percentage: 50,
      };

      (authApi.authenticatedFetch as jest.Mock).mockResolvedValue(mockRegionDetail);

      const result = await journeyApi.getRegionDetails('shire');

      expect(authApi.authenticatedFetch).toHaveBeenCalledWith(
        '/api/journey/regions/shire',
        {
          method: 'GET',
        }
      );
      expect(result).toEqual(mockRegionDetail);
    });

    it('handles region not found', async () => {
      (authApi.authenticatedFetch as jest.Mock).mockRejectedValue(
        new Error('Region not found')
      );

      await expect(journeyApi.getRegionDetails('invalid')).rejects.toThrow(
        'Region not found'
      );
    });
  });

  describe('listRegions', () => {
    it('fetches all regions successfully', async () => {
      const mockRegions = [
        {
          name: 'shire',
          display_name: 'The Shire',
          difficulty_level: 'beginner',
          map_coordinates: { x: 100, y: 150 },
          is_unlocked: true,
          knowledge_points_required: 0,
        },
        {
          name: 'bree',
          display_name: 'Bree',
          difficulty_level: 'beginner',
          map_coordinates: { x: 200, y: 200 },
          is_unlocked: true,
          knowledge_points_required: 50,
        },
      ];

      (authApi.authenticatedFetch as jest.Mock).mockResolvedValue(mockRegions);

      const result = await journeyApi.listRegions();

      expect(authApi.authenticatedFetch).toHaveBeenCalledWith('/api/journey/regions', {
        method: 'GET',
      });
      expect(result).toEqual(mockRegions);
      expect(result).toHaveLength(2);
    });
  });

  describe('listPaths', () => {
    it('fetches all journey paths successfully', async () => {
      const mockPaths = [
        {
          name: 'fellowship',
          display_name: 'The Fellowship of the Ring',
          description: 'Follow the Fellowship',
          ordered_regions: ['shire', 'bree', 'rivendell'],
          narrative_theme: 'Classic LOTR',
          estimated_duration_hours: 10,
          path_color: '#4A90E2',
        },
      ];

      (authApi.authenticatedFetch as jest.Mock).mockResolvedValue(mockPaths);

      const result = await journeyApi.listPaths();

      expect(authApi.authenticatedFetch).toHaveBeenCalledWith('/api/journey/paths', {
        method: 'GET',
      });
      expect(result).toEqual(mockPaths);
      expect(result).toHaveLength(1);
    });
  });

  describe('listAchievements', () => {
    it('fetches all achievements successfully', async () => {
      const mockAchievements = [
        {
          code: 'first_steps',
          name: 'First Steps',
          description: 'Complete your first quiz',
          category: 'learning',
          rarity: 'common',
          icon_name: 'star',
          badge_color: '#FFD700',
          is_earned: true,
        },
        {
          code: 'shire_master',
          name: 'Shire Master',
          description: 'Master all Shire quizzes',
          category: 'exploration',
          rarity: 'rare',
          icon_name: 'trophy',
          badge_color: '#C0392B',
          is_earned: false,
        },
      ];

      (authApi.authenticatedFetch as jest.Mock).mockResolvedValue(mockAchievements);

      const result = await journeyApi.listAchievements();

      expect(authApi.authenticatedFetch).toHaveBeenCalledWith(
        '/api/journey/achievements',
        {
          method: 'GET',
        }
      );
      expect(result).toEqual(mockAchievements);
      expect(result).toHaveLength(2);
    });
  });

  describe('error handling', () => {
    it('handles network errors', async () => {
      (authApi.authenticatedFetch as jest.Mock).mockRejectedValue(
        new Error('Network request failed')
      );

      await expect(journeyApi.getJourneyState()).rejects.toThrow(
        'Network request failed'
      );
    });

    it('handles authentication errors', async () => {
      (authApi.authenticatedFetch as jest.Mock).mockRejectedValue(
        new Error('Unauthorized')
      );

      await expect(journeyApi.travelToRegion('shire')).rejects.toThrow(
        'Unauthorized'
      );
    });
  });
});
