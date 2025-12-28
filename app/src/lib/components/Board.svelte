<script lang="ts">
  import Icon from '@iconify/svelte';
  import { onMount } from 'svelte';
  import { fly } from 'svelte/transition';
  import { allQuestions, type Board, type Question, UiMode } from '$lib/state.svelte';
  import type { AudioClient } from '../audio.svelte';
  import { gameState } from '../game-state.svelte';
  import QuestionDisplay from './QuestionDisplay.svelte';

  let { mode, board, audio }: { board: Board; mode: UiMode, audio: AudioClient } = $props();

  let hoveredQuestion = $state<Question | undefined>(undefined);
  let selectedQuestion = $state<Question | undefined>(undefined);
  let sidebarQuestion = $derived(hoveredQuestion || selectedQuestion ||
    allQuestions(board).find(q => q.id === gameState.selectedQuestion));

  function isColumnVisible(categoryId: number): boolean {
    return gameState.visibleCategories.has(categoryId);
  }

  function handleQuestionClick(question: Question) {
    if (mode === 'host') {
      console.log(question, selectedQuestion);
      if (selectedQuestion?.id === question.id) {
        selectedQuestion = undefined;
      } else {
        selectedQuestion = question;
      }
    }
  }

  function presentQuestion(question: Question) {
    gameState.websocket?.toggleBuzzers(true);
    gameState.websocket?.selectQuestion(question.id);
  }
</script>

<div class="grid gap-4 p-2" class:grid-cols-[3fr,1fr]={mode === 'host'} class:grid-cols-1={mode === 'presentation'}>
  {#if board}
    <div class="grid grid-cols-6 gap-2">
      {#each board.categories as category}
        <div class="flex flex-col gap-2" class:opacity-50={mode === 'host' && !isColumnVisible(category.id)}>
          <button
            class="h-24 bg-primary-700 rounded-md font-bold p-2 text-center uppercase text-2xl hover:bg-primary-600 transition-colors"
            onclick={() => mode === 'host' && gameState.websocket?.revealCategory(category.id)}
          >
            {#if mode === UiMode.Host || isColumnVisible(category.id)}
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
                  {audio}
                  visible={gameState.selectedQuestion === question.id && mode === 'presentation'}
                />
                {#if (mode === UiMode.Host || isColumnVisible(category.id)) && !gameState.answeredQuestions.has(question.id)}
                  <div transition:fly={{ x: 100 }}>{question.points}</div>
                {/if}
              </button>
            {/each}
          </div>
        </div>
      {/each}
    </div>

    {#if mode === 'host' && sidebarQuestion}
      <div class="bg-surface-800 p-4 rounded-lg border-primary-500 {gameState.selectedQuestion === sidebarQuestion.id && 'border-2'} transition-all"
      transition:fly={{ x: 100 }}>
        <h3 class="text-xl mb-4">
          {#if sidebarQuestion.special}
            <Icon icon="mdi:star" class="text-warning-400 inline" />
          {/if}
          {sidebarQuestion.points} - {sidebarQuestion.text}
        </h3>
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
            onclick={() => gameState.websocket?.updateQuestionStatus(sidebarQuestion.id, true)}
          >
            Mark Answered
          </button>
          <button
            type="button"
            class="btn btn-variant-ringed"
            onclick={() => gameState.websocket?.updateQuestionStatus(sidebarQuestion.id, false)}
          >
            Skip
          </button>
          <button
            type="button"
            class="btn btn-variant-filled"
            onclick={() => gameState.websocket?.selectQuestion(undefined)}
          >
            Complete
          </button>
        </div>
      </div>
    {/if}
  {/if}
</div>
