<script lang="ts">
	import { gameState } from '$lib/stores';
	import Icon from '@iconify/svelte';
	import { allQuestions, type Game, type Player, type Team, type UiMode } from '../state.svelte';

	const { mode, game }: { mode: UiMode, game: Game } = $props();
	
	let websocket = $derived($gameState.websocket);

	let currentQuestion = $derived(allQuestions($gameState.board)
		.find(q => q.id === $gameState.selectedQuestion));
	let pointsToAward = $state(0);
	$effect(() => {
		pointsToAward = currentQuestion?.points ?? 0;
	});

	function recordAnswer(playerId: number, correct: boolean) {
		websocket.recordPlayerAnswer(playerId, currentQuestion.id, correct,
			correct ? pointsToAward : -pointsToAward);
	}

	function toggleBuzzers(state?: boolean) {
		websocket.toggleBuzzers(state ?? !$gameState.buzzersEnabled);
	}

	function getScore(entity: Team | Player) {
		if ('players' in entity) {
			return entity.players.reduce((acc, player) => acc + $gameState.scores[player.id] ?? 0, 0);
		}
		return $gameState.scores[entity.id] ?? 0;
	}
</script>

<div class="fixed bottom-0 left-0 right-0 bg-surface-800 p-4">
	{#if mode === 'host'}
		<div class="flex justify-between items-center mb-4">
			<div class="flex gap-2">
				<h3 class="text-xl font-bold">{currentQuestion?.points} eggs</h3>
				<input class="input variant-form-material" title="Points to award" type="number" bind:value={pointsToAward} />
			</div>
			<button
				class="px-4 py-2 rounded {$gameState.activeBuzzerId !== null ? 'bg-orange-600' : $gameState.buzzersEnabled ? 'bg-red-600' : 'bg-green-600'}"
				onclick={() => $gameState.activeBuzzerId !== null ? toggleBuzzers(true) : toggleBuzzers()}
			>
				{$gameState.activeBuzzerId !== null ? 'Reset' : $gameState.buzzersEnabled ? 'Disable' : 'Enable'} Buzzers
			</button>
		</div>
	{/if}

	<div class="grid grid-cols-{game.teams.length} gap-4">
		{#each game.teams as team}
			<div class="bg-surface-700 rounded-lg p-4" style="background-color: {team.color}">
				<div class="flex justify-between items-center">
					<h4 class="text-lg font-bold">{team.name}</h4>
					<span class="text-2xl">{getScore(team)} eggs</span>
				</div>

				{#if mode === 'host'}
					<div class="space-y-2 mt-2">
						{#each team.players as player}
							<div
								class="flex justify-between items-center p-2 rounded"
								class:bg-primary-600={$gameState.activeBuzzerId === player.buzzer}
							>
								<span>{player.name}</span>
								<div class="flex gap-2">
									<span>{getScore(player)} eggs</span>
									{#if currentQuestion}
										<button
											class="btn-icon variant-filled-success text-2xl"
											onclick={() => recordAnswer(player.id, true)}
										>
											<Icon icon="mdi:plus" />
										</button>
										<button
											class="btn-icon variant-filled-error text-2xl"
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
					<div class="flex justify-center items-center gap-2">
						{#each team.players as player}
							<span class="chip text-md {$gameState.activeBuzzerId === player.buzzer ? 'variant-filled-primary' : 'variant-ghost-secondary'}">{player.name}</span>
							{/each}
					</div>
				{/if}
			</div>
		{/each}
	</div>
</div>
