<script lang="ts">
  import { page } from '$app/state';
  import { AudioClient } from '$lib/audio.svelte';
  import Board from '$lib/components/Board.svelte';
  import BoardSelector from '$lib/components/BoardSelector.svelte';
  import ScoreFooter from '$lib/components/ScoreFooter.svelte';
  import { UiMode } from '$lib/state.svelte.js';
  import { gameState } from '$lib/stores';
  import { GameWebSocket } from '$lib/websocket';
  import { onDestroy, onMount } from 'svelte';

  const gameId = page.params.game;
  const mode = page.params.mode as UiMode || UiMode.Presentation;

  let { data: game } = $props();

  let websocket: GameWebSocket | undefined = $state(undefined);
  let audioClient: AudioClient | undefined = $state(undefined);

  onMount(async () => {
    audioClient = mode === UiMode.Presentation ? new AudioClient() : undefined;
    $gameState.scores = Object.fromEntries(game.teams.flatMap((team) =>
      team.players.map((player) => [player.id, player.score])));
    websocket = new GameWebSocket(gameId, mode, audioClient);
    $gameState.websocket = websocket;
  });

  onDestroy(() => {
    audioClient?.dispose();
  });
</script>

<div class="min-h-screen bg-surface-900 text-surface-50">
  {#if mode === 'host'}
    <BoardSelector {game} {websocket} />
  {/if}
  {#if $gameState.board}
    <Board board={$gameState.board} {mode} {websocket} audio={audioClient} />
  {/if}
  <ScoreFooter {mode} {game} {websocket} />
</div>
