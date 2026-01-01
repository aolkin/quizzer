import { ENDPOINT, type Board, type Question } from './state.svelte';

async function apiRequest<T>(
  url: string,
  method: string,
  body: object | undefined,
  errorMessage: string,
): Promise<T> {
  const options: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };

  if (body !== undefined) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`http://${ENDPOINT}${url}`, options);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`${errorMessage}: ${response.statusText} - ${error}`);
  }

  return await response.json();
}

export async function recordPlayerAnswer(
  boardId: number,
  playerId: number,
  questionId: number,
  isCorrect: boolean,
  points?: number,
): Promise<{ player_id: number; score: number; version: number }> {
  return apiRequest(
    `/api/board/${boardId}/answers/`,
    'POST',
    { player_id: playerId, question_id: questionId, is_correct: isCorrect, points },
    'Failed to record answer',
  );
}

export async function toggleQuestion(
  questionId: number,
  answered: boolean,
): Promise<{ question_id: number; answered: boolean; version: number }> {
  return apiRequest(
    `/api/question/${questionId}/`,
    'PATCH',
    { answered },
    'Failed to toggle question',
  );
}

export async function getBoard(boardId: number): Promise<Board> {
  return apiRequest(`/api/board/${boardId}/`, 'GET', undefined, 'Failed to fetch board');
}

export interface MediaFile {
  id: number;
  url: string;
  original_filename: string;
  file_size: number;
  uploaded_at: string;
}

export async function listMedia(): Promise<MediaFile[]> {
  return apiRequest('/api/media/', 'GET', undefined, 'Failed to list media files');
}

export interface QuestionUpdateRequest {
  text?: string;
  answer?: string;
  points?: number;
  slides?: Array<{
    text?: string;
    media_type?: 'image' | 'video' | 'audio';
    media_url?: string;
    answer?: string;
  }>;
}

export async function getQuestion(questionId: number): Promise<Question> {
  return apiRequest(`/api/questions/${questionId}/`, 'GET', undefined, 'Failed to fetch question');
}

export async function updateQuestion(
  questionId: number,
  updates: QuestionUpdateRequest,
): Promise<Question> {
  return apiRequest(`/api/questions/${questionId}/`, 'PATCH', updates, 'Failed to update question');
}
