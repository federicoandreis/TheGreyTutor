// quizApi.ts
// Service for interacting with the backend quiz API endpoints

export const BASE_URL = 'http://192.168.0.225:8000';

export interface QuizSession {
  session_id: string;
  student_id: string;
  student_name: string;
  questions_asked: number;
  correct: number;
  incorrect: number;
  current_question: any;
  finished: boolean;
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
  session_id: string;
}

export async function startQuizSession(student_id: string, student_name: string) {
  const res = await fetch(`${BASE_URL}/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id, student_name }),
  });
  if (!res.ok) throw new Error('Failed to start quiz session');
  return await res.json();
}

export async function getNextQuestion(session_id: string) {
  const res = await fetch(`${BASE_URL}/session/${session_id}/question`);
  if (!res.ok) throw new Error('Failed to get next question');
  return await res.json();
}

export async function submitQuizAnswer(session_id: string, answer: string) {
  const res = await fetch(`${BASE_URL}/session/${session_id}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answer }),
  });
  if (!res.ok) throw new Error('Failed to submit answer');
  return await res.json();
}

export async function getQuizSessionState(session_id: string) {
  const res = await fetch(`${BASE_URL}/session/${session_id}`);
  if (!res.ok) throw new Error('Failed to get session state');
  return await res.json();
}
