/**
 * Quiz API endpoints
 * 
 * Handles quiz sessions, questions, and answer submissions
 */

import { get, post } from './apiClient';

/**
 * API Types
 */
export interface QuizSessionParams {
  student_id: string;
  student_name: string;
  community?: string;
  difficulty?: number;
  num_questions?: number;
}

export interface QuizSession {
  session_id: string;
  question: Question;
  question_number: number;
  total_questions: number;
}

export interface Question {
  id: string;
  text: string;
  type: 'multiple_choice' | 'true_false' | 'open_ended';
  options?: string[];
  correct_answer?: string;
}

export interface AnswerSubmission {
  answer: string;
}

export interface AnswerResponse {
  is_correct: boolean;
  feedback: string;
  correct_answer?: string;
  next_question?: Question;
  knowledge_points_earned: number;
  session_complete: boolean;
}

export interface SessionSummary {
  session_id: string;
  total_questions: number;
  correct_answers: number;
  total_points: number;
  accuracy: number;
}

/**
 * Create a new quiz session
 */
export const createQuizSession = async (
  params: QuizSessionParams = {}
): Promise<QuizSession> => {
  return post<QuizSession>('/session', params);
};

/**
 * Get the next question in a session
 * Backend returns QuestionResponse: { question: {...}, session_id: string, question_number: number }
 */
export const getNextQuestion = async (sessionId: string): Promise<any> => {
  return get<any>(`/session/${sessionId}/question`);
};

/**
 * Submit an answer for the current question
 */
export const submitAnswer = async (
  sessionId: string,
  answer: string
): Promise<AnswerResponse> => {
  return post<AnswerResponse>(`/session/${sessionId}/answer`, { answer });
};

/**
 * Get session details and summary
 */
export const getSessionSummary = async (sessionId: string): Promise<SessionSummary> => {
  return get<SessionSummary>(`/session/${sessionId}`);
};
