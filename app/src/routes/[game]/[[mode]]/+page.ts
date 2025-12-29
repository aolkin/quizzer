import { ENDPOINT } from '$lib/state.svelte.js';
import type { Game } from '$lib/state.svelte.js';

export const load = async ({
  params,
  fetch,
}: {
  params: { game: string };
  fetch: typeof globalThis.fetch;
}): Promise<Game> => {
  const response = await fetch(`http://${ENDPOINT}/api/game/${params.game}/`);
  const game = await response.json();
  return game as Game;
};
