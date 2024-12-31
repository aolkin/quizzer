export interface Question {
	id: number,
	text: string,
	type: string,
	answer: string,
	media_url?: string,
	order: number,
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

export interface Game {
	id: number;
	name: string;
	mode: string;
	boards: Array<Pick<Board, 'id' | 'name' | 'order'>>;
	teams: Array<{
		id: number;
		name: string;
		players: Array<Player>;
	}>;
}

export function allQuestions(board?: Board): Question[] {
	return board?.categories.flatMap(c => c.questions) ?? [];
}

export const ENDPOINT = 'quasar.local:8000';

export enum UiMode {
	Host = 'host',
	Presentation = 'presentation',
}
