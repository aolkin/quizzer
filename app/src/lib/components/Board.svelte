<script lang="ts">
  import Icon from '@iconify/svelte';
  import { fly } from 'svelte/transition';
  import { toggleQuestion } from '$lib/api';
  import { allQuestions, type Board, type Question, UiMode, type Slide } from '$lib/state.svelte';
  import type { AudioClient } from '../audio.svelte';
  import { gameState } from '../game-state.svelte';
  import { formatInlineMarkdown } from '../markdown';
  import QuestionDisplay from './QuestionDisplay.svelte';

  let { mode, board, audio }: { board: Board; mode: UiMode; audio?: AudioClient } = $props();

  let hoveredQuestion = $state<Question | undefined>(undefined);
  let selectedQuestion = $state<Question | undefined>(undefined);
  let sidebarQuestion = $derived(
    hoveredQuestion ||
      selectedQuestion ||
      allQuestions(board).find((q) => q.id === gameState.selectedQuestion),
  );

  const currentSlide = $derived<Slide | null>(
    sidebarQuestion?.type === 'slides' && sidebarQuestion.slides[gameState.currentSlideIndex]
      ? sidebarQuestion.slides[gameState.currentSlideIndex]
      : null,
  );

  const totalSlides = $derived(sidebarQuestion?.slides?.length || 0);

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

  function nextSlide() {
    const newIndex = gameState.currentSlideIndex + 1;
    if (newIndex < totalSlides) {
      gameState.websocket?.setSlide(newIndex);
    }
  }

  function previousSlide() {
    const newIndex = gameState.currentSlideIndex - 1;
    if (newIndex >= 0) {
      gameState.websocket?.setSlide(newIndex);
    }
  }
</script>

<div
  class="grid gap-4 p-2"
  class:grid-cols-[3fr,1fr]={mode === 'host'}
  class:grid-cols-1={mode === 'presentation'}
>
  {#if board}
    <div class="grid grid-cols-6 gap-2">
      {#each board.categories as category}
        <div
          class="flex flex-col gap-2"
          class:opacity-50={mode === 'host' && !isColumnVisible(category.id)}
        >
          <button
            class="h-24 rounded-md bg-primary-700 p-2 text-center text-2xl font-bold uppercase transition-colors hover:bg-primary-600"
            onclick={() => mode === 'host' && gameState.websocket?.revealCategory(category.id)}
            data-testid="category-{category.id}"
          >
            {#if mode === UiMode.Host || isColumnVisible(category.id)}
              <div transition:fly={{ x: 100 }}>{category.name}</div>
            {/if}
          </button>

          <div class="flex flex-col gap-2">
            {#each category.questions as question, questionIndex}
              <button
                class="flex aspect-video items-center justify-center rounded-md bg-primary-800 text-8xl font-bold transition-colors hover:bg-primary-700"
                class:opacity-75={gameState.answeredQuestions.has(question.id)}
                onclick={() => handleQuestionClick(question)}
                onmouseenter={() => mode === 'host' && (hoveredQuestion = question)}
                onmouseleave={() => mode === 'host' && (hoveredQuestion = undefined)}
                data-testid="question-{category.order}-{questionIndex}"
              >
                <QuestionDisplay
                  {question}
                  {audio}
                  visible={gameState.selectedQuestion === question.id && mode === 'presentation'}
                  slideIndex={gameState.currentSlideIndex}
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
      <div
        class="rounded-lg border-primary-500 bg-surface-800 p-4 {gameState.selectedQuestion ===
          sidebarQuestion.id && 'border-2'} transition-all"
        transition:fly={{ x: 100 }}
      >
        <h3 class="mb-4 text-xl">
          {#if sidebarQuestion.flags.includes('dino')}
            <Icon icon="mdi:star" class="inline text-warning-400" />
          {/if}
          <!-- eslint-disable-next-line svelte/no-at-html-tags -->
          {@html formatInlineMarkdown(sidebarQuestion.text)}
          <span class="text-sm text-primary-300">{sidebarQuestion.points} points</span>
        </h3>

        {#if sidebarQuestion.type === 'text'}
          <p class="mb-4 text-primary-400" data-testid="question-answer">
            {sidebarQuestion.answer}
          </p>
        {:else if sidebarQuestion.type === 'slides'}
          <div class="mb-4">
            <p class="mb-2 text-sm text-primary-300">
              Slide {gameState.currentSlideIndex + 1} of {totalSlides}
            </p>
            {#if currentSlide}
              {#if currentSlide.text}
                <p class="mb-2 text-primary-200">{currentSlide.text}</p>
              {/if}
              {#if currentSlide.media_type && currentSlide.media_url}
                {#if currentSlide.media_type === 'image'}
                  <img
                    src={currentSlide.media_url}
                    alt="Slide preview"
                    class="mb-2 max-h-40 rounded"
                  />
                {:else}
                  <p class="mb-2 text-sm italic text-primary-400">
                    {currentSlide.media_type}: {currentSlide.media_url}
                  </p>
                {/if}
              {/if}
              {#if currentSlide.answer}
                <p class="text-primary-400" data-testid="slide-answer">
                  Answer: {currentSlide.answer}
                </p>
              {/if}
            {/if}
            <p class="mt-2 text-primary-400" data-testid="question-answer">
              Overall: {sidebarQuestion.answer}
            </p>
          </div>
        {/if}

        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            class="btn-variant-filled btn"
            onclick={() => presentQuestion(sidebarQuestion)}
            data-testid="present-question"
          >
            Present
          </button>

          {#if sidebarQuestion.type === 'slides' && totalSlides > 1}
            <button
              type="button"
              class="btn-variant-filled btn"
              onclick={() => previousSlide()}
              disabled={gameState.currentSlideIndex === 0}
              data-testid="previous-slide"
            >
              ← Previous
            </button>
            <button
              type="button"
              class="btn-variant-filled btn"
              onclick={() => nextSlide()}
              disabled={gameState.currentSlideIndex >= totalSlides - 1}
              data-testid="next-slide"
            >
              Next →
            </button>
          {/if}

          <button
            type="button"
            class="btn-variant-filled btn"
            onclick={() => toggleQuestion(sidebarQuestion.id, true)}
            data-testid="mark-answered"
          >
            Mark Answered
          </button>
          <button
            type="button"
            class="btn-variant-ringed btn"
            onclick={() => toggleQuestion(sidebarQuestion.id, false)}
            data-testid="skip-question"
          >
            Skip
          </button>
          <button
            type="button"
            class="btn-variant-filled btn"
            onclick={() => gameState.websocket?.selectQuestion(undefined)}
            data-testid="complete-question"
          >
            Complete
          </button>
        </div>
      </div>
    {/if}
  {/if}
</div>
