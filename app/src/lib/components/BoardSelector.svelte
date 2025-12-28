<script lang="ts">
    import Icon from '@iconify/svelte';
    import { gameState } from '$lib/stores';
    import type { Game } from '../state.svelte';

    const { game }: { game: Game } = $props();
    
    let websocket = $derived($gameState.websocket);
</script>

<header class="bg-surface-800 p-2 mb-2">
    <div class="flex items-center justify-between">
        <h1 class="text-xl font-bold">{game.name || 'Loading...'}</h1>

        <div class="flex gap-2">
        {#each game.boards as board}
            <button
              class="chip {$gameState.currentBoard === board.id ? 'variant-filled' : 'variant-soft'} text-surface-50"
              onclick={() => websocket.selectBoard(board.id)}
            >
                {#if $gameState.currentBoard === board.id}<Icon icon="mdi:check" class="mr-1" />{/if}
                <span>{board.name}</span>
            </button>
        {/each}
            </div>
    </div>
</header>
