/**
 * Quiz API - Updated to use centralized API client from Phase 1.1
 * 
 * Provides backward-compatible wrapper functions for existing quiz functionality
 * in ChatScreen while using the new centralized API infrastructure.
 */

import {
  createQuizSession,
  getNextQuestion as apiGetNextQuestion,
  submitAnswer as apiSubmitAnswer,
  getSessionSummary,
  QuizSession as ApiQuizSession,
  Question,
  AnswerResponse,
} from './api/quiz';
import { config } from '../utils/config';

// Export BASE_URL for backward compatibility
export const BASE_URL = config.apiUrl;

// Legacy interfaces for backward compatibility with ChatScreen
export interface QuizSession {
  session_id: string;
  student_id?: string;
  student_name?: string;
  questions_asked?: number;
  correct?: number;
  incorrect?: number;
  current_question?: any;
  finished?: boolean;
}

export interface QuestionResponse {
  question: any;
  session_id: string;
  question_number: number;
}

export interface SubmitAnswerResponse {
  correct: boolean;
  quality?: number;
  feedback?: any;
  next_question?: any;
  session_complete: boolean;
  session_id?: string;
}

/**
 * Start a new quiz session
 * Maps old parameters to new API
 */
export async function startQuizSession(
  student_id: string,
  student_name: string
): Promise<QuizSession> {
  try {
    const session = await createQuizSession({
      student_id,
      student_name,
      // community: undefined, // Can be added later
      // difficulty: undefined,
      num_questions: 10, // Default number
    });

    return {
      session_id: session.session_id,
      student_id,
      student_name,
      questions_asked: session.question_number - 1,
      correct: 0,
      incorrect: 0,
      current_question: session.question,
      finished: false,
    };
  } catch (error) {
    console.error('[quizApi] Failed to start quiz session:', error);
    throw new Error('Failed to start quiz session');
  }
}

/**
 * Get the next question in a quiz session
 * Backend already returns QuestionResponse format, just pass it through
 */
export async function getNextQuestion(session_id: string): Promise<QuestionResponse> {
  try {
    // apiGetNextQuestion returns the full QuestionResponse from backend
    const response = await apiGetNextQuestion(session_id);
    return response;
  } catch (error) {
    console.error('[quizApi] Failed to get next question:', error);
    throw new Error('Failed to get next question');
  }
}

/**
 * Submit an answer for the current question
 */
export async function submitQuizAnswer(
  session_id: string,
  answer: string
): Promise<SubmitAnswerResponse> {
  try {
    const response = await apiSubmitAnswer(session_id, answer);

    // Backend returns: { correct, quality, feedback: {explanation, strengths, weaknesses, suggestions}, ... }
    // Pass through directly without transformation
    return {
      correct: response.correct,
      quality: response.quality,
      feedback: response.feedback,  // Already an object, don't wrap again
      next_question: response.next_question,
      session_complete: response.session_complete,
      session_id: response.session_id || session_id,
    };
  } catch (error) {
    console.error('[quizApi] Failed to submit answer:', error);
    throw new Error('Failed to submit answer');
  }
}

/**
 * Get quiz session state
 */
export async function getQuizSessionState(session_id: string): Promise<any> {
  try {
    const summary = await getSessionSummary(session_id);
    return summary;
  } catch (error) {
    console.error('[quizApi] Failed to get session state:', error);
    throw new Error('Failed to get session state');
  }
}
