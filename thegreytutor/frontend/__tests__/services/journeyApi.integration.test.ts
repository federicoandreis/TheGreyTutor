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
      expect(state.unlocked_regions).toBeDefined();
      expect(Array.isArray(state.unlocked_regions)).toBe(true);
    });

    it('should include region details in the state', async () => {
      const state = await journeyApi.getJourneyState();

      expect(state.region_statuses).toBeDefined();
      expect(Array.isArray(state.region_statuses)).toBe(true);

      if (state.region_statuses.length > 0) {
        const region = state.region_statuses[0];
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
      expect(firstRegion.difficulty_level).toBeDefined();
    });

    it('should return regions with valid difficulty levels', async () => {
      const regions = await journeyApi.listRegions();
      const validLevels = ['beginner', 'intermediate', 'advanced', 'expert'];

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
      // Region data may be in region_data or message
      expect(result.message || result.region_data).toBeDefined();
    });

    it('should return failure for locked region (not throw)', async () => {
      // Backend returns { success: false } for locked regions instead of throwing
      const lockedRegion = 'mordor'; // Usually locked initially

      const result = await journeyApi.travelToRegion(lockedRegion);
      
      expect(result).toBeDefined();
      expect(result.success).toBe(false);
      expect(result.message).toBeDefined();
    });
  });

  describe('listPaths', () => {
    it('should fetch journey paths (may be empty if none configured)', async () => {
      const paths = await journeyApi.listPaths();

      expect(paths).toBeDefined();
      expect(Array.isArray(paths)).toBe(true);
      // Paths may be empty if none are configured in the database
      
      if (paths.length > 0) {
        const firstPath = paths[0];
        expect(firstPath.name).toBeDefined();
        expect(firstPath.display_name).toBeDefined();
        expect(firstPath.description).toBeDefined();
        expect(firstPath.ordered_regions).toBeDefined();
        expect(Array.isArray(firstPath.ordered_regions)).toBe(true);
      }
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
      // Backend expects score as float 0.0-1.0, questions_answered >= 1
      const quizData = {
        region_name: 'shire',
        quiz_id: `test-quiz-${Date.now()}`,
        score: 0.8, // 80% as decimal
        questions_answered: 10,
        answers: [
          { question_id: 'q1', selected: 'Bag End', correct: true },
          { question_id: 'q2', selected: 'Gandalf', correct: true },
        ],
      };

      const result = await journeyApi.completeQuiz(quizData);

      expect(result).toBeDefined();
      expect(result.knowledge_points_earned).toBeDefined();
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
    // Note: Network error test removed - changing env var at runtime doesn't affect
    // already-initialized service that captured the URL at import time

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
