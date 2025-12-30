export interface Question {
  id: number;
  text: string;
  type: string;
  flags: string[];
  answer: string;
  media_url?: string;
  order?: number;
  points: number;
  answered: boolean;
}

export interface Board {
  name: string;
  id: number;
  order: number;
  categories: Array<{
    name: string;
    order: number;
    id: number;
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
  points_term: string;
  boards: Array<Pick<Board, 'id' | 'name' | 'order'>>;
  teams: Array<Team>;
}

export function allQuestions(board?: Board): Question[] {
  return board?.categories.flatMap((c) => c.questions) ?? [];
}

export const ENDPOINT =
  typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_ENDPOINT
    ? import.meta.env.VITE_API_ENDPOINT
    : 'quasar.local:8000';

export enum UiMode {
  Host = 'host',
  Presentation = 'presentation',
}

// Version tracking for preventing out-of-order updates
const playerVersions = new Map<number, number>();
const questionVersions = new Map<number, number>();

function shouldUpdate(
  versionMap: Map<number, number>,
  entityId: number,
  version: number,
  entityType: string,
): boolean {
  const currentVersion = versionMap.get(entityId) ?? 0;
  if (version >= currentVersion) {
    versionMap.set(entityId, version);
    return true;
  }
  console.log(`Ignoring stale ${entityType} update: version ${version} < ${currentVersion}`);
  return false;
}

export function shouldUpdatePlayer(playerId: number, version: number): boolean {
  return shouldUpdate(playerVersions, playerId, version, 'player');
}

export function shouldUpdateQuestion(questionId: number, version: number): boolean {
  return shouldUpdate(questionVersions, questionId, version, 'question');
}
