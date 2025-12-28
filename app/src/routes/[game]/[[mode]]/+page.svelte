<script lang="ts">
  import { page } from '$app/state';
  import { AudioClient } from '$lib/audio.svelte';
  import Board from '$lib/components/Board.svelte';
  import BoardSelector from '$lib/components/BoardSelector.svelte';
  import ScoreFooter from '$lib/components/ScoreFooter.svelte';
  import { UiMode } from '$lib/state.svelte.js';
  import { gameState } from '$lib/game-state.svelte';
  import { GameWebSocket } from '$lib/websocket';
  import { onDestroy, onMount } from 'svelte';

  const gameId = page.params.game;
  const mode = (page.params.mode as UiMode) || UiMode.Presentation;

  let { data: game } = $props();

  let audioClient: AudioClient | undefined = $state(undefined);

  onMount(async () => {
    audioClient = mode === UiMode.Presentation ? new AudioClient() : undefined;
    gameState.setScores(
      Object.fromEntries(
        game.teams.flatMap((team) => team.players.map((player) => [player.id, player.score])),
      ),
    );
    gameState.setWebsocket(new GameWebSocket(gameId, mode, audioClient));
  });

  onDestroy(() => {
    audioClient?.dispose();
  });
</script>

<div class="min-h-screen bg-surface-900 text-surface-50">
  {#if mode === 'host'}
    <BoardSelector {game} />
  {/if}
  {#if gameState.board}
    <Board board={gameState.board} {mode} audio={audioClient} />
  {/if}
  <ScoreFooter {mode} {game} />
</div>
