<script lang="ts">
  import { recordPlayerAnswer } from '$lib/api';
  import { gameState } from '$lib/game-state.svelte';
  import Icon from '@iconify/svelte';
  import { allQuestions, type Game, type Player, type Team, type UiMode } from '../state.svelte';

  const { mode, game }: { mode: UiMode; game: Game } = $props();

  let currentQuestion = $derived(
    allQuestions(gameState.board).find((q) => q.id === gameState.selectedQuestion),
  );
  let pointsToAward = $state(0);
  let buzzerLogLevel = $state<'WARN' | 'DEBUG'>('WARN');

  $effect(() => {
    pointsToAward = currentQuestion?.points ?? 0;
  });

  async function recordAnswer(playerId: number, correct: boolean) {
    if (!currentQuestion || !gameState.currentBoard) return;
    await recordPlayerAnswer(
      gameState.currentBoard,
      playerId,
      currentQuestion.id,
      correct,
      correct ? pointsToAward : -pointsToAward,
    );
  }

  function toggleBuzzers(state?: boolean) {
    gameState.websocket?.toggleBuzzers(state ?? !gameState.buzzersEnabled);
  }

  function toggleBuzzerLogLevel() {
    buzzerLogLevel = buzzerLogLevel === 'WARN' ? 'DEBUG' : 'WARN';
    gameState.websocket?.setBuzzerLogLevel(buzzerLogLevel);
  }

  function getScore(entity: Team | Player) {
    if ('players' in entity) {
      return entity.players.reduce((acc, player) => acc + (gameState.scores[player.id] ?? 0), 0);
    }
    return gameState.scores[entity.id] ?? 0;
  }
</script>

<div class="fixed bottom-0 left-0 right-0 bg-surface-800 p-4">
  {#if mode === 'host'}
    <div class="mb-4 flex items-center justify-between">
      <div class="flex gap-2">
        <h3 class="text-xl font-bold">{currentQuestion?.points} {game.points_term}</h3>
        <input
          class="input variant-form-material"
          title="Points to award"
          type="number"
          bind:value={pointsToAward}
        />
      </div>
      <div class="flex items-center gap-2">
        <button
          class="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full {gameState.buzzerConnected
            ? 'bg-green-600'
            : 'bg-red-600'}"
          onclick={toggleBuzzerLogLevel}
          title="Buzzer {gameState.buzzerConnected
            ? 'connected'
            : 'disconnected'} - Click to toggle log level ({buzzerLogLevel})"
        >
          <span class="text-xs font-bold">{buzzerLogLevel === 'DEBUG' ? 'D' : 'W'}</span>
        </button>
        <button
          class="rounded px-4 py-2 {gameState.activeBuzzerId !== null
            ? 'bg-orange-600'
            : gameState.buzzersEnabled
              ? 'bg-red-600'
              : 'bg-green-600'}"
          onclick={() =>
            gameState.activeBuzzerId !== null ? toggleBuzzers(true) : toggleBuzzers()}
        >
          {gameState.activeBuzzerId !== null
            ? 'Reset'
            : gameState.buzzersEnabled
              ? 'Disable'
              : 'Enable'} Buzzers
        </button>
      </div>
    </div>
  {/if}

  <div class="grid grid-cols-{game.teams.length} gap-4">
    {#each game.teams as team}
      <div class="rounded-lg bg-surface-700 p-4" style="background-color: {team.color}">
        <div class="flex items-center justify-between">
          <h4 class="text-lg font-bold">{team.name}</h4>
          <span class="text-2xl">{getScore(team)} {game.points_term}</span>
        </div>

        {#if mode === 'host'}
          <div class="mt-2 space-y-2">
            {#each team.players as player}
              <div
                class="flex items-center justify-between rounded p-2"
                class:bg-primary-600={gameState.activeBuzzerId === player.buzzer}
              >
                <span>{player.name}</span>
                <div class="flex gap-2">
                  <span>{getScore(player)} {game.points_term}</span>
                  {#if currentQuestion}
                    <button
                      class="variant-filled-success btn-icon text-2xl"
                      onclick={() => recordAnswer(player.id, true)}
                    >
                      <Icon icon="mdi:plus" />
                    </button>
                    <button
                      class="variant-filled-error btn-icon text-2xl"
                      onclick={() => recordAnswer(player.id, false)}
                    >
                      <Icon icon="mdi:minus" />
                    </button>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="flex items-center justify-center gap-2">
            {#each team.players as player}
              <span
                class="text-md chip {gameState.activeBuzzerId === player.buzzer
                  ? 'variant-filled-primary'
                  : 'variant-ghost-secondary'}">{player.name}</span
              >
            {/each}
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>
