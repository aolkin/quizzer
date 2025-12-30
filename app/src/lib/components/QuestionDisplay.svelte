<script lang="ts">
  import { type AudioClient, Sound } from '../audio.svelte';
  import type { Question } from '../state.svelte';

  const {
    question,
    visible,
    audio,
  }: { question: Question; visible: boolean; audio?: AudioClient } = $props();

  let container: HTMLDivElement;

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
      if (question.special) {
        container.style.transform = 'rotate3d(1, 0, 0, 720deg)';
        audio?.play(Sound.Special);
      }
    }
  });
</script>

<div
  bind:this={container}
  class="flex items-center justify-center overflow-hidden transition-all {question.special
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
          {question.text}
        </h2>
      {:else if question.type === 'image'}
        <img
          src={question.media_url}
          alt="Question media"
          class="mx-auto max-w-full rounded-lg shadow-lg"
        />
      {:else if question.type === 'video'}
        <!-- svelte-ignore a11y_media_has_caption -->
        <video src={question.media_url} controls class="mx-auto max-w-full rounded-lg shadow-lg"
        ></video>
      {:else if question.type === 'audio'}
        <audio src={question.media_url} controls class="w-full"></audio>
      {/if}
    </div>
  </div>
</div>
