<script lang="ts">
    import { gameState } from '$lib/stores';
		import type { UiMode } from '../state.svelte';
		import type { GameWebSocket } from '../websocket';

		const { mode, websocket }: { mode: UiMode, websocket: GameWebSocket } = $props();

		let activeBuzzerId: number | undefined = $state(undefined);

    function handlePointsUpdate(playerId: number, points: number) {
        websocket.updatePlayerScore(playerId, points);
    }

    function toggleBuzzers() {
        websocket.toggleBuzzers(!$gameState.buzzersEnabled);
    }
</script>

<div class="fixed bottom-0 left-0 right-0 bg-surface-800 p-4">
    {#if mode === 'host'}
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-xl font-bold">Current Question: {$gameState.selectedQuestion?.points || 0} points</h3>
            <button
                class="px-4 py-2 rounded"
                class:bg-green-600={!$gameState.buzzersEnabled}
                class:bg-red-600={$gameState.buzzersEnabled}
                on:click={toggleBuzzers}
            >
                {$gameState.buzzersEnabled ? 'Disable' : 'Enable'} Buzzers
            </button>
        </div>
    {/if}

    <div class="grid grid-cols-3 gap-4">
        {#each $gameState.teams as team}
            <div class="bg-surface-700 rounded-lg p-4">
                <div class="flex justify-between items-center mb-4">
                    <h4 class="text-lg font-bold">{team.name}</h4>
                    <span class="text-2xl">{team.score} pts</span>
                </div>

                {#if mode === 'host'}
                    <div class="space-y-2">
                        {#each team.players as player}
                            <div
                                class="flex justify-between items-center p-2 rounded"
                                class:bg-primary-600={activeBuzzerId === player.id}
                            >
                                <span>{player.name}</span>
                                <div class="flex gap-2">
                                    <span>{player.score} pts</span>
                                    {#if $gameState.selectedQuestion}
                                        <button
                                            class="px-2 py-1 bg-green-600 rounded"
                                            on:click={() => handlePointsUpdate(
                                                player.id,
                                                $gameState.selectedQuestion.points
                                            )}
                                        >
                                            +
                                        </button>
                                        <button
                                            class="px-2 py-1 bg-red-600 rounded"
                                            on:click={() => handlePointsUpdate(
                                                player.id,
                                                -$gameState.selectedQuestion.points
                                            )}
                                        >
                                            -
                                        </button>
                                    {/if}
                                </div>
                            </div>
                        {/each}
                    </div>
                {/if}
            </div>
        {/each}
    </div>
</div>
