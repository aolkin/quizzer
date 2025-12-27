export interface Question {
	id: number,
	text: string,
	type: string,
	special: boolean,
	answer: string,
	media_url?: string,
	order?: number,
	points: number,
	answered: boolean,
}

export interface Board {
	name: string;
	id: number;
	order: number;
	categories: Array<{
		name: string,
		order: number,
		id: number,
		questions: Array<Question>;
	}>;
}

export interface Player {
	id: number;
	name: string;
	buzzer?: number;
	score: number;
}

export interface Team {
	id: number;
	name: string;
	color: string;
	players: Array<Player>;
}

export interface Game {
	id: number;
	name: string;
	mode: string;
	boards: Array<Pick<Board, 'id' | 'name' | 'order'>>;
	teams: Array<Team>;
}

export function allQuestions(board?: Board): Question[] {
	return board?.categories.flatMap(c => c.questions) ?? [];
}

export const ENDPOINT = 'quasar.local:8000';

export enum UiMode {
	Host = 'host',
	Presentation = 'presentation',
}

// Version tracking for preventing out-of-order updates
const playerVersions = new Map<number, number>();
const questionVersions = new Map<number, number>();

export function shouldUpdatePlayer(playerId: number, version: number): boolean {
	const currentVersion = playerVersions.get(playerId) ?? 0;
	if (version >= currentVersion) {
		playerVersions.set(playerId, version);
		return true;
	}
	console.log(`Ignoring stale player update: version ${version} < ${currentVersion}`);
	return false;
}

export function shouldUpdateQuestion(questionId: number, version: number): boolean {
	const currentVersion = questionVersions.get(questionId) ?? 0;
	if (version >= currentVersion) {
		questionVersions.set(questionId, version);
		return true;
	}
	console.log(`Ignoring stale question update: version ${version} < ${currentVersion}`);
	return false;
}
