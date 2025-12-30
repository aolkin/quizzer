<script lang="ts">
  import { type AudioClient, Sound } from '../audio.svelte';
  import { formatInlineMarkdown } from '../markdown';
  import type { Question } from '../state.svelte';

  const {
    question,
    visible,
    audio,
    showingAnswer = false,
  }: {
    question: Question;
    visible: boolean;
    audio?: AudioClient;
    showingAnswer?: boolean;
  } = $props();

  let container: HTMLDivElement;

  const hasDinoFlag = $derived(question.flags.includes('dino'));

  // Determine which media URL to use - answer if showing answer and available, otherwise question
  const mediaUrl = $derived(
    showingAnswer && question.media_answer_url ? question.media_answer_url : question.media_url,
  );

  $effect(() => {
    if (!visible && container.parentElement) {
      const originRect = container.parentElement.getBoundingClientRect();

      // Initial position matching the original box
      container.style.zIndex = '-1';
      container.style.top = `${originRect.top}px`;
      container.style.left = `${originRect.left}px`;
      container.style.width = `${originRect.width}px`;
      container.style.height = `${originRect.height}px`;
      container.style.transform = 'initial';
    } else {
      // Trigger animation to full screen
      container.style.top = '0';
      container.style.left = '0';
      container.style.width = '100vw';
      container.style.height = '100vh';
      container.style.zIndex = '50';
      if (hasDinoFlag) {
        container.style.transform = 'rotate3d(1, 0, 0, 720deg)';
        audio?.play(Sound.Dino);
      }
    }
  });
</script>

<div
  bind:this={container}
  class="flex items-center justify-center overflow-hidden transition-all {hasDinoFlag
    ? 'bg-warning-800 duration-[2000ms]'
    : 'bg-primary-900 duration-500'} fixed"
  style="container-type: inline-size"
  data-testid="question-display"
>
  <div class="mx-auto max-w-[60%] text-center">
    <div>
      {#if question.type === 'text'}
        <h2
          class="font-bold"
          style="font-size: 3cqw; line-height: 3.5cqw;"
          data-testid="question-text"
        >
          <!-- eslint-disable-next-line svelte/no-at-html-tags -- HTML is escaped in formatInlineMarkdown -->
          {@html formatInlineMarkdown(question.text)}
        </h2>
      {:else if question.type === 'image'}
        <img src={mediaUrl} alt="Question media" class="mx-auto max-w-full rounded-lg shadow-lg" />
      {:else if question.type === 'video'}
        <!-- svelte-ignore a11y_media_has_caption -->
        <video src={mediaUrl} controls class="mx-auto max-w-full rounded-lg shadow-lg"></video>
      {:else if question.type === 'audio'}
        <audio src={mediaUrl} controls class="w-full"></audio>
      {/if}
    </div>
  </div>
</div>
