<script lang="ts">
  import { AudioClient } from '$lib/audio.svelte';
  import Board from '$lib/components/Board.svelte';
  import BoardSelector from '$lib/components/BoardSelector.svelte';
  import ConnectionStatusOverlay from '$lib/components/ConnectionStatusOverlay.svelte';
  import ScoreFooter from '$lib/components/ScoreFooter.svelte';
  import { UiMode, type Player, type Team } from '$lib/state.svelte.js';
  import { gameState } from '$lib/game-state.svelte';
  import { GameWebSocket } from '$lib/websocket';
  import { onDestroy, onMount } from 'svelte';
  import type { PageProps } from './$types';

  let { params, data: game }: PageProps = $props();

  const gameId = $derived(params.game);
  const mode = $derived((params.mode as UiMode) || UiMode.Presentation);

  let audioClient: AudioClient | undefined = $state(undefined);

  onMount(async () => {
    audioClient = mode === UiMode.Presentation ? new AudioClient() : undefined;
    gameState.setScores(
      Object.fromEntries(
        game.teams.flatMap((team: Team) =>
          team.players.map((player: Player) => [player.id, player.score]),
        ),
      ),
    );
    gameState.setWebsocket(new GameWebSocket(gameId, mode, audioClient));
  });

  onDestroy(() => {
    audioClient?.dispose();
  });
</script>

<div class="min-h-screen bg-surface-900 text-surface-50">
  {#if mode === UiMode.Host}
    <BoardSelector {game} />
    <ConnectionStatusOverlay {gameState} />
  {/if}
  {#if gameState.board}
    <Board board={gameState.board} {mode} audio={audioClient} />
  {/if}
  <ScoreFooter {mode} {game} />
</div>
