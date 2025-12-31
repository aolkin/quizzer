import { error } from '@sveltejs/kit';
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

  if (!response.ok) {
    throw error(response.status, `Game ${params.game} not found`);
  }

  const game = await response.json();
  return game as Game;
};
