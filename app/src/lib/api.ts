import { ENDPOINT } from './state.svelte';

async function apiRequest<T>(
	url: string,
	method: string,
	body: object,
	errorMessage: string
): Promise<T> {
	const response = await fetch(`http://${ENDPOINT}${url}`, {
		method,
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});

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
	points?: number
): Promise<{ player_id: number; score: number; version: number }> {
	return apiRequest(
		`/api/board/${boardId}/answers/`,
		'POST',
		{ player_id: playerId, question_id: questionId, is_correct: isCorrect, points },
		'Failed to record answer'
	);
}

export async function toggleQuestion(
	questionId: number,
	answered: boolean
): Promise<{ question_id: number; answered: boolean; version: number }> {
	return apiRequest(
		`/api/question/${questionId}/`,
		'PATCH',
		{ answered },
		'Failed to toggle question'
	);
}
