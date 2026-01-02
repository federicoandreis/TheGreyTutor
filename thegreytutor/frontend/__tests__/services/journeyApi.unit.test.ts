/**
 * Unit Tests for Journey API
 *
 * These tests use MOCKED authApi (fast, isolated tests).
 * The authApi mock is configured in jest.setup.unit.js
 *
 * Run with: npm run test:unit
 */

import { journeyApi } from '../../src/services/journeyApi';
import { authApi } from '../../src/services/authApi';

// authApi is already mocked by jest.setup.unit.js
const mockAuthenticatedFetch = authApi.authenticatedFetch as jest.MockedFunction<
  typeof authApi.authenticatedFetch
>;

describe('JourneyApi Unit Tests', () => {
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

      mockAuthenticatedFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => mockJourneyState,
      } as Response);

      const result = await journeyApi.getJourneyState();

      expect(mockAuthenticatedFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/journey/state')
      );
      expect(result).toEqual(mockJourneyState);
    });

    it('throws error when fetch fails', async () => {
      mockAuthenticatedFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      } as Response);

      await expect(journeyApi.getJourneyState()).rejects.toThrow(
        'Failed to get journey state'
      );
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
          description: 'A town of Men',
          difficulty_level: 'beginner',
          lore_depth: 'medium',
          available_quiz_themes: ['history', 'characters'],
          lore_snippets: [],
          visit_count: 1,
          completion_percentage: 0,
        },
      };

      mockAuthenticatedFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => mockResponse,
      } as Response);

      const result = await journeyApi.travelToRegion('bree');

      expect(mockAuthenticatedFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/journey/travel'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ region_name: 'bree' }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('handles travel failure', async () => {
      mockAuthenticatedFetch.mockResolvedValue({
        ok: false,
        status: 403,
        statusText: 'Forbidden',
      } as Response);

      await expect(journeyApi.travelToRegion('rivendell')).rejects.toThrow(
        'Failed to travel to region'
      );
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

      mockAuthenticatedFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => mockResponse,
      } as Response);

      const quizData = {
        region_name: 'shire',
        quiz_id: 'quiz-123',
        score: 0.8,
        questions_answered: 10,
        answers: [],
      };

      const result = await journeyApi.completeQuiz(quizData);

      expect(mockAuthenticatedFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/journey/complete-quiz'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(quizData),
        })
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
            description: 'Master all Shire quizzes',
            category: 'region' as const,
            rarity: 'rare' as const,
          },
        ],
        regions_unlocked: ['bree'],
      };

      mockAuthenticatedFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => mockResponse,
      } as Response);

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
        difficulty_level: 'beginner',
        map_coordinates: { x: 100, y: 150, radius: 20 },
        prerequisite_regions: [],
        knowledge_points_required: 0,
        available_quiz_themes: ['hobbits', 'farming'],
        is_unlocked: true,
        can_unlock: true,
        completion_percentage: 50,
      };

      mockAuthenticatedFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => mockRegionDetail,
      } as Response);

      const result = await journeyApi.getRegionDetails('shire');

      expect(mockAuthenticatedFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/journey/regions/shire')
      );
      expect(result).toEqual(mockRegionDetail);
    });

    it('handles region not found', async () => {
      mockAuthenticatedFetch.mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      } as Response);

      await expect(journeyApi.getRegionDetails('invalid')).rejects.toThrow(
        'Failed to get region details'
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

      mockAuthenticatedFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => mockRegions,
      } as Response);

      const result = await journeyApi.listRegions();

      expect(mockAuthenticatedFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/journey/regions')
      );
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

      mockAuthenticatedFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => mockPaths,
      } as Response);

      const result = await journeyApi.listPaths();

      expect(mockAuthenticatedFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/journey/paths')
      );
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
          category: 'quiz' as const,
          rarity: 'common' as const,
          icon_name: 'star',
          badge_color: '#FFD700',
          is_earned: true,
        },
        {
          code: 'shire_master',
          name: 'Shire Master',
          description: 'Master all Shire quizzes',
          category: 'region' as const,
          rarity: 'rare' as const,
          icon_name: 'trophy',
          badge_color: '#C0392B',
          is_earned: false,
        },
      ];

      mockAuthenticatedFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => mockAchievements,
      } as Response);

      const result = await journeyApi.listAchievements();

      expect(mockAuthenticatedFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/journey/achievements')
      );
      expect(result).toEqual(mockAchievements);
      expect(result).toHaveLength(2);
    });
  });

  describe('error handling', () => {
    it('handles network errors', async () => {
      mockAuthenticatedFetch.mockRejectedValue(new Error('Network request failed'));

      await expect(journeyApi.getJourneyState()).rejects.toThrow(
        'Network request failed'
      );
    });

    it('handles authentication errors', async () => {
      mockAuthenticatedFetch.mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
      } as Response);

      await expect(journeyApi.travelToRegion('shire')).rejects.toThrow(
        'Failed to travel to region'
      );
    });

    it('handles server errors', async () => {
      mockAuthenticatedFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      } as Response);

      await expect(journeyApi.listRegions()).rejects.toThrow('Failed to list regions');
    });
  });
});
