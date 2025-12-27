import { ENDPOINT } from './state.svelte';

export async function recordPlayerAnswer(
	boardId: number,
	playerId: number,
	questionId: number,
	isCorrect: boolean,
	points?: number
): Promise<{ playerId: number; score: number; version: number }> {
	const response = await fetch(`http://${ENDPOINT}/api/board/${boardId}/answers/`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ playerId, questionId, isCorrect, points })
	});

	if (!response.ok) {
		const error = await response.text();
		throw new Error(`Failed to record answer: ${response.statusText} - ${error}`);
	}

	const data = await response.json();
	return { playerId: data.playerId, score: data.score, version: data.version };
}

export async function toggleQuestion(
	questionId: number,
	answered: boolean
): Promise<{ questionId: number; answered: boolean; version: number }> {
	const response = await fetch(`http://${ENDPOINT}/api/question/${questionId}/`, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ answered })
	});

	if (!response.ok) {
		const error = await response.text();
		throw new Error(`Failed to toggle question: ${response.statusText} - ${error}`);
	}

	const data = await response.json();
	return { questionId: data.questionId, answered: data.answered, version: data.version };
}
