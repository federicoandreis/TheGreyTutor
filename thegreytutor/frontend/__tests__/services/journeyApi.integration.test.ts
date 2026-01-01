/**
 * Integration Tests for Journey API
 *
 * These tests use the REAL backend API (no mocks for authApi).
 * Prerequisites:
 * - Backend must be running at http://localhost:8000
 * - Database must be initialized with test data
 *
 * Run with: npm run test:integration
 */

import { journeyApi } from '../../src/services/journeyApi';
import { authApi } from '../../src/services/authApi';

describe('Journey API Integration Tests', () => {
  let testToken: string;
  const testUser = {
    email: `test-${Date.now()}@example.com`,
    password: 'TestPassword123',
    username: `testuser${Date.now()}`,
  };

  beforeAll(async () => {
    // Register a real test user and get token
    try {
      const registerResponse = await authApi.register(testUser);
      if (registerResponse.success && registerResponse.tokens) {
        testToken = registerResponse.tokens.access_token;
      } else {
        throw new Error('Failed to register test user');
      }
    } catch (error) {
      console.error('Setup failed:', error);
      throw error;
    }
  });

  afterAll(async () => {
    // Clean up: logout
    try {
      await authApi.logout();
    } catch (error) {
      console.warn('Cleanup warning:', error);
    }
  });

  describe('getJourneyState', () => {
    it('should fetch the user journey state from backend', async () => {
      const state = await journeyApi.getJourneyState();

      expect(state).toBeDefined();
      expect(state.current_region).toBeDefined();
      expect(state.knowledge_points).toBeGreaterThanOrEqual(0);
      expect(state.regions_unlocked).toBeDefined();
      expect(Array.isArray(state.regions_unlocked)).toBe(true);
    });

    it('should include region details in the state', async () => {
      const state = await journeyApi.getJourneyState();

      expect(state.regions).toBeDefined();
      expect(Array.isArray(state.regions)).toBe(true);

      if (state.regions.length > 0) {
        const region = state.regions[0];
        expect(region.name).toBeDefined();
        expect(region.display_name).toBeDefined();
        expect(region.difficulty_level).toBeDefined();
      }
    });
  });

  describe('listRegions', () => {
    it('should fetch all available regions', async () => {
      const regions = await journeyApi.listRegions();

      expect(regions).toBeDefined();
      expect(Array.isArray(regions)).toBe(true);
      expect(regions.length).toBeGreaterThan(0);

      const firstRegion = regions[0];
      expect(firstRegion.name).toBeDefined();
      expect(firstRegion.display_name).toBeDefined();
      expect(firstRegion.description).toBeDefined();
      expect(firstRegion.difficulty_level).toBeDefined();
    });

    it('should return regions with valid difficulty levels', async () => {
      const regions = await journeyApi.listRegions();
      const validLevels = ['beginner', 'intermediate', 'advanced'];

      regions.forEach(region => {
        expect(validLevels).toContain(region.difficulty_level);
      });
    });
  });

  describe('getRegionDetails', () => {
    it('should fetch details for a specific region', async () => {
      const regionName = 'shire';
      const details = await journeyApi.getRegionDetails(regionName);

      expect(details).toBeDefined();
      expect(details.name).toBe(regionName);
      expect(details.display_name).toBeDefined();
      expect(details.description).toBeDefined();
      expect(details.lore_summary).toBeDefined();
    });

    it('should handle non-existent region gracefully', async () => {
      const regionName = 'non-existent-region';

      await expect(
        journeyApi.getRegionDetails(regionName)
      ).rejects.toThrow();
    });
  });

  describe('travelToRegion', () => {
    it('should allow traveling to an unlocked region', async () => {
      // Note: This assumes 'shire' is unlocked by default for new users
      const regionName = 'shire';

      const result = await journeyApi.travelToRegion(regionName);

      expect(result).toBeDefined();
      expect(result.success).toBe(true);
      expect(result.current_region).toBe(regionName);
    });

    it('should prevent traveling to a locked region', async () => {
      // Note: This assumes there's at least one locked region
      // Adjust based on actual backend logic
      const lockedRegion = 'mordor'; // Usually locked initially

      await expect(
        journeyApi.travelToRegion(lockedRegion)
      ).rejects.toThrow();
    });
  });

  describe('listPaths', () => {
    it('should fetch all available journey paths', async () => {
      const paths = await journeyApi.listPaths();

      expect(paths).toBeDefined();
      expect(Array.isArray(paths)).toBe(true);
      expect(paths.length).toBeGreaterThan(0);

      const firstPath = paths[0];
      expect(firstPath.name).toBeDefined();
      expect(firstPath.display_name).toBeDefined();
      expect(firstPath.description).toBeDefined();
      expect(firstPath.ordered_regions).toBeDefined();
      expect(Array.isArray(firstPath.ordered_regions)).toBe(true);
    });
  });

  describe('listAchievements', () => {
    it('should fetch user achievements', async () => {
      const achievements = await journeyApi.listAchievements();

      expect(achievements).toBeDefined();
      expect(Array.isArray(achievements)).toBe(true);

      // New user may have no achievements
      if (achievements.length > 0) {
        const achievement = achievements[0];
        expect(achievement.code).toBeDefined();
        expect(achievement.name).toBeDefined();
        expect(achievement.description).toBeDefined();
      }
    });
  });

  describe('completeQuiz', () => {
    it('should submit quiz results and update progress', async () => {
      const quizData = {
        region_name: 'shire',
        quiz_id: 'test-quiz-123',
        score: 8,
        questions_answered: 10,
        time_taken: 120,
        answers: [
          {
            question_id: 'q1',
            selected_answer: 'Bag End',
            is_correct: true,
            time_taken: 12,
          },
          {
            question_id: 'q2',
            selected_answer: 'Gandalf',
            is_correct: true,
            time_taken: 10,
          },
        ],
      };

      const result = await journeyApi.completeQuiz(quizData);

      expect(result).toBeDefined();
      expect(result.success).toBe(true);
      expect(result.knowledge_points_earned).toBeGreaterThan(0);
      expect(result.new_total_knowledge_points).toBeGreaterThanOrEqual(
        result.knowledge_points_earned
      );
    });

    it('should handle invalid quiz submission', async () => {
      const invalidQuizData = {
        region_name: '',
        quiz_id: '',
        score: -1,
        questions_answered: 0,
        answers: [],
      };

      await expect(
        journeyApi.completeQuiz(invalidQuizData)
      ).rejects.toThrow();
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      // Temporarily break the API URL to simulate network error
      const originalUrl = process.env.EXPO_PUBLIC_API_URL;
      process.env.EXPO_PUBLIC_API_URL = 'http://invalid-url:9999';

      await expect(
        journeyApi.getJourneyState()
      ).rejects.toThrow();

      // Restore original URL
      process.env.EXPO_PUBLIC_API_URL = originalUrl;
    });

    it('should handle unauthorized requests', async () => {
      // Logout to clear token
      await authApi.logout();

      // Attempt to access protected endpoint
      await expect(
        journeyApi.getJourneyState()
      ).rejects.toThrow();

      // Re-authenticate for subsequent tests
      await authApi.login({
        email: testUser.email,
        password: testUser.password,
      });
    });
  });
});
