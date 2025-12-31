<script lang="ts">
  import { type AudioClient, Sound } from '../audio.svelte';
  import { formatInlineMarkdown } from '../markdown';
  import type { Question, Slide } from '../state.svelte';

  const {
    question,
    visible,
    audio,
    slideIndex = 0,
  }: { question: Question; visible: boolean; audio?: AudioClient; slideIndex?: number } = $props();

  let container: HTMLDivElement;

  const hasDinoFlag = $derived(question.flags.includes('dino'));

  const isSlideIndexValid = $derived(
    question.type !== 'slides' || (slideIndex >= 0 && slideIndex < question.slides.length),
  );

  const currentSlide = $derived<Slide | null>(
    question.type === 'slides' && isSlideIndexValid ? question.slides[slideIndex] : null,
  );

  const displayText = $derived(
    question.type === 'slides' && currentSlide?.text ? currentSlide.text : question.text,
  );

  $effect(() => {
    if (!visible && container.parentElement) {
      const originRect = container.parentElement.getBoundingClientRect();

      container.style.zIndex = '-1';
      container.style.top = `${originRect.top}px`;
      container.style.left = `${originRect.left}px`;
      container.style.width = `${originRect.width}px`;
      container.style.height = `${originRect.height}px`;
      container.style.transform = 'initial';
    } else {
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
      {#if question.type === 'text' || !currentSlide?.media_type}
        <h2
          class="font-bold"
          style="font-size: 3cqw; line-height: 3.5cqw;"
          data-testid="question-text"
        >
          <!-- eslint-disable-next-line svelte/no-at-html-tags -->
          {@html formatInlineMarkdown(displayText)}
        </h2>
      {:else if currentSlide.media_type === 'image'}
        <img
          src={currentSlide.media_url}
          alt="Question media"
          class="mx-auto max-w-full rounded-lg shadow-lg"
        />
      {:else if currentSlide.media_type === 'video'}
        <!-- svelte-ignore a11y_media_has_caption -->
        <video src={currentSlide.media_url} controls class="mx-auto max-w-full rounded-lg shadow-lg"
        ></video>
      {:else if currentSlide.media_type === 'audio'}
        <audio src={currentSlide.media_url} controls class="w-full"></audio>
      {/if}
    </div>
  </div>
</div>
