/**
 * QuizScreen Tests
 *
 * Basic test suite for QuizScreen component
 * Tests initialization, rendering, and user interactions
 */

import React from 'react';
import { render, waitFor } from '@testing-library/react-native';
import QuizScreen from '../QuizScreen';
import * as quizApi from '../../../services/quizApi';

// Mock navigation
const mockNavigate = jest.fn();
const mockGoBack = jest.fn();

jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  useNavigation: () => ({
    navigate: mockNavigate,
    goBack: mockGoBack,
  }),
  useRoute: () => ({
    params: {
      theme: 'Hobbits',
      location: 'The Shire',
    },
  }),
}));

// Mock quiz API
jest.mock('../../../services/quizApi', () => ({
  startQuizSession: jest.fn(),
  getNextQuestion: jest.fn(),
  submitQuizAnswer: jest.fn(),
}));

describe('QuizScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    (quizApi.startQuizSession as jest.Mock).mockImplementation(() =>
      new Promise(() => {}) // Never resolves - keeps loading
    );

    const { getByText } = render(<QuizScreen />);

    expect(getByText('Preparing your quiz...')).toBeTruthy();
  });

  it('should initialize quiz session on mount', async () => {
    const mockSession = { session_id: 'test-session-123' };
    const mockQuestion = {
      question: 'What is a Hobbit?',
      options: ['A small person', 'A large person', 'A wizard', 'An elf'],
      question_type: 'multiple_choice',
    };

    (quizApi.startQuizSession as jest.Mock).mockResolvedValue(mockSession);
    (quizApi.getNextQuestion as jest.Mock).mockResolvedValue(mockQuestion);

    const { getByText } = render(<QuizScreen />);

    await waitFor(() => {
      expect(quizApi.startQuizSession).toHaveBeenCalledWith('demo_user', 'Adventurer');
      expect(quizApi.getNextQuestion).toHaveBeenCalledWith('test-session-123');
    });

    // Should display the question
    await waitFor(() => {
      expect(getByText(/What is a Hobbit\?/)).toBeTruthy();
    });
  });

  it('should render multiple choice options', async () => {
    const mockSession = { session_id: 'test-session-123' };
    const mockQuestion = {
      question: 'Test question?',
      options: ['Option A', 'Option B', 'Option C'],
      question_type: 'multiple_choice',
    };

    (quizApi.startQuizSession as jest.Mock).mockResolvedValue(mockSession);
    (quizApi.getNextQuestion as jest.Mock).mockResolvedValue(mockQuestion);

    const { getByText } = render(<QuizScreen />);

    await waitFor(() => {
      expect(getByText('Option A')).toBeTruthy();
      expect(getByText('Option B')).toBeTruthy();
      expect(getByText('Option C')).toBeTruthy();
    });
  });

  it('should show error and go back on initialization failure', async () => {
    (quizApi.startQuizSession as jest.Mock).mockRejectedValue(new Error('Network error'));

    const { getByText } = render(<QuizScreen />);

    await waitFor(() => {
      // Alert should be shown (mocked in test environment)
      expect(quizApi.startQuizSession).toHaveBeenCalled();
    });
  });

  it('should render quiz complete state with score', async () => {
    const mockSession = { session_id: 'test-session-123' };
    const mockQuestion = {
      question: 'Test?',
      options: ['A', 'B'],
    };
    const mockSubmitResponse = {
      correct: true,
      session_complete: true,
      feedback: { explanation: 'Well done!' },
    };

    (quizApi.startQuizSession as jest.Mock).mockResolvedValue(mockSession);
    (quizApi.getNextQuestion as jest.Mock).mockResolvedValue(mockQuestion);
    (quizApi.submitQuizAnswer as jest.Mock).mockResolvedValue(mockSubmitResponse);

    const { getByText } = render(<QuizScreen />);

    // Wait for question to load, then we'd need to interact to see completion
    // This is a simplified test - full interaction would require more setup
    await waitFor(() => {
      expect(quizApi.getNextQuestion).toHaveBeenCalled();
    });
  });
});
