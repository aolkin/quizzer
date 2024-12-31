<script lang="ts">
    import { fade } from 'svelte/transition';
    import type { Question } from '../state.svelte';

    const { question, visible }: { question: Question, visible: boolean } = $props();

    let container: HTMLDivElement;
    let questionText: HTMLElement | undefined;

    $effect(() => {
        if (!visible) {
            const originRect = container.parentElement.getBoundingClientRect();

            // Initial position matching the original box
            container.style.zIndex = '-1';
            container.style.position = 'fixed';
            container.style.top = `${originRect.top}px`;
            container.style.left = `${originRect.left}px`;
            container.style.width = `${originRect.width}px`;
            container.style.height = `${originRect.height}px`;
            if (questionText) {
                //questionText.style.fontSize = '.5rem';
                //questionText.style.lineHeight = '.75rem';
            }
        } else {
            // Trigger animation to full screen
            container.style.top = '0';
            container.style.left = '0';
            container.style.width = '100vw';
            container.style.height = '100vh';
            container.style.zIndex = '50';
            if (questionText) {
                //questionText.style.fontSize = '2.5rem';
                //questionText.style.lineHeight = '2.75rem';
            }
        }
    });
</script>

<div
  bind:this={container}
  class="bg-primary-900 flex items-center justify-center overflow-hidden transition-all duration-500"
  style="container-type: inline-size"
>
    <div
      class="max-w-[60%] mx-auto text-center"
    >
        <div>
            {#if question.type === 'text'}
                <h2 class="font-bold"
                    style="font-size: 3cqw; line-height: 3.5cqw;"
                    bind:this={questionText}>{question.text}</h2>
            {:else if question.type === 'image'}
                <img
                  src={question.media_url}
                  alt="Question media"
                  class="max-w-full mx-auto rounded-lg shadow-lg"
                />
            {:else if question.type === 'video'}
                <video
                  src={question.media_url}
                  controls
                  class="max-w-full mx-auto rounded-lg shadow-lg"
                />
            {:else if question.type === 'audio'}
                <audio
                  src={question.media_url}
                  controls
                  class="w-full"
                />
            {/if}
        </div>
    </div>
</div>
