<script lang="ts">
  import Icon from '@iconify/svelte';
  import { gameState } from '$lib/game-state.svelte';
  import type { Game } from '../state.svelte';

  const { game }: { game: Game } = $props();
</script>

<header class="mb-2 bg-surface-800 p-2">
  <div class="flex items-center justify-between">
    <h1 class="text-xl font-bold">{game.name || 'Loading...'}</h1>

    <div class="flex gap-2">
      {#each game.boards as board}
        <button
          class="chip {gameState.currentBoard === board.id
            ? 'variant-filled'
            : 'variant-soft'} text-surface-50"
          onclick={() => gameState.websocket?.selectBoard(board.id)}
          data-testid="board-selector-{board.id}"
        >
          {#if gameState.currentBoard === board.id}<Icon icon="mdi:check" class="mr-1" />{/if}
          <span>{board.name}</span>
        </button>
      {/each}
    </div>
  </div>
</header>
