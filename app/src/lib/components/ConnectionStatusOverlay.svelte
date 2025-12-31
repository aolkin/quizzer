<script lang="ts">
  import type { GameStateManager } from '$lib/game-state.svelte';

  interface Props {
    gameState: GameStateManager;
  }

  let { gameState }: Props = $props();

  // Sort clients: connected first, then by type
  const sortedClients = $derived(
    Array.from(gameState.clientConnections.values()).sort((a, b) => {
      if (a.connected !== b.connected) return a.connected ? -1 : 1;
      return a.clientType.localeCompare(b.clientType);
    }),
  );
</script>

<div
  role="status"
  aria-label="Client connection status"
  class="pointer-events-none fixed right-4 top-4 z-50 opacity-70 transition-opacity duration-300 hover:opacity-30"
>
  <div class="min-w-[200px] rounded-lg bg-surface-800 p-3 shadow-lg">
    <h3 class="mb-2 text-xs font-semibold text-surface-300">Clients</h3>

    {#if sortedClients.length === 0}
      <p class="text-xs italic text-surface-400">No clients connected</p>
    {:else}
      <ul class="space-y-1">
        {#each sortedClients as client}
          <li class="flex items-center justify-between text-xs">
            <div class="flex items-center gap-2">
              <span class="text-lg {client.connected ? 'text-green-500' : 'text-red-500'}">
                {client.connected ? '🟢' : '🔴'}
              </span>
              <span class="text-surface-200">
                {client.clientType}
                {#if client.clientId}
                  <span class="text-surface-400">({client.clientId})</span>
                {/if}
              </span>
            </div>

            {#if client.latency !== undefined}
              <span class="ml-2 text-surface-400">
                {client.latency}ms
              </span>
            {/if}
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>
