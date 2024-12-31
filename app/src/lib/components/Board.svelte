<script lang="ts">
  import { onMount } from 'svelte';
  import { fly } from 'svelte/transition';
  import { allQuestions, type Board, type Question, UiMode } from '$lib/state.svelte';
  import { gameState } from '../stores';
  import { GameWebSocket } from '../websocket';
  import QuestionDisplay from './QuestionDisplay.svelte';

  let { mode, board }: { board: Board; mode: UiMode } = $props();

  let websocket: GameWebSocket | undefined = $derived($gameState.websocket);
  let hoveredQuestion = $state(undefined);
  let selectedQuestion = $state(undefined);
  let sidebarQuestion = $derived(hoveredQuestion || selectedQuestion ||
    allQuestions(board).find(q => q.id === $gameState.selectedQuestion));

  function isColumnVisible(categoryId: number): boolean {
    return $gameState.visibleCategories.has(categoryId);
  }

  function handleQuestionClick(question: Question) {
    if (mode === 'host') {
      if (selectedQuestion?.id === question.id) {
        selectedQuestion = null;
      } else {
        selectedQuestion = question;
      }
    }
  }

  function presentQuestion(question: Question) {
    websocket?.toggleBuzzers(true);
    websocket?.selectQuestion(question.id);
  }
</script>

<div class="grid gap-4 p-2" class:grid-cols-[3fr,1fr]={mode === 'host'} class:grid-cols-1={mode === 'presentation'}>
  {#if board}
    <div class="grid grid-cols-6 gap-2">
      {#each board.categories as category}
        <div class="flex flex-col gap-2" class:opacity-50={mode === 'host' && !isColumnVisible(category.id)}>
          <button
            class="h-24 bg-primary-700 rounded-md font-bold p-2 text-center uppercase text-4xl hover:bg-primary-600 transition-colors"
            onclick={() => mode === 'host' && websocket.revealCategory(category.id)}
          >
            {#if mode === 'host' || isColumnVisible(category.id)}
              <div transition:fly={{ x: 100 }}>{category.name}</div>
            {/if}
          </button>

          <div class="flex flex-col gap-2">
            {#each category.questions as question}
              <button
                class="aspect-video bg-primary-800 rounded-md flex items-center justify-center text-8xl font-bold hover:bg-primary-700 transition-colors"
                class:opacity-75={question.status === 'answered'}
                onclick={() => handleQuestionClick(question)}
                onmouseenter={() => mode === 'host' && (hoveredQuestion = question)}
                onmouseleave={() => mode === 'host' && (hoveredQuestion = undefined)}
              >
                <QuestionDisplay
                  {question}
                  visible={$gameState.selectedQuestion === question.id && mode === 'presentation'}
                />
                {#if isColumnVisible(category.id) && !$gameState.answeredQuestions.has(question.id)}
                  <div transition:fly={{ x: 100 }}>{question.points}</div>
                {/if}
              </button>
            {/each}
          </div>
        </div>
      {/each}
    </div>

    {#if mode === 'host' && sidebarQuestion}
      <div class="bg-surface-800 p-4 rounded-lg">
        <h3 class="text-xl mb-4">{sidebarQuestion.text}</h3>
        <p class="text-primary-400 mb-4">{sidebarQuestion.answer}</p>
        <div class="flex gap-2">
          <button
            type="button"
            class="btn btn-variant-filled"
            onclick={() => presentQuestion(sidebarQuestion)}
          >
            Present
          </button>
          <button
            type="button"
            class="btn btn-variant-filled"
            onclick={() => websocket.updateQuestionStatus(sidebarQuestion.id, true)}
          >
            Mark Answered
          </button>
          <button
            type="button"
            class="btn btn-variant-ringed"
            onclick={() => websocket.updateQuestionStatus(sidebarQuestion.id, false)}
          >
            Skip
          </button>
          <button
            type="button"
            class="btn btn-variant-filled"
            onclick={() => websocket.selectQuestion(undefined)}
          >
            Complete
          </button>
        </div>
      </div>
    {/if}
  {/if}
</div>
