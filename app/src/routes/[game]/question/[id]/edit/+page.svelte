<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import type { Slide } from '$lib/state.svelte';
  import { getQuestion, updateQuestion, type QuestionUpdateRequest } from '$lib/api';
  import SlideEditor from '$lib/components/SlideEditor.svelte';

  let questionId = $derived(Number($page.params.id));
  let gameId = $derived(Number($page.params.game));

  let text = $state('');
  let answer = $state('');
  let points = $state(0);
  let slides = $state<Slide[]>([]);
  let loading = $state(true);
  let saving = $state(false);
  let error = $state<string | undefined>(undefined);

  onMount(async () => {
    await loadQuestion();
  });

  async function loadQuestion() {
    loading = true;
    error = undefined;
    try {
      const question = await getQuestion(questionId);
      text = question.text;
      answer = question.answer;
      points = question.points;
      slides = [...question.slides];
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load question';
    } finally {
      loading = false;
    }
  }

  function addSlide() {
    slides = [...slides, {}];
  }

  function updateSlide(index: number, slide: Slide) {
    slides[index] = slide;
  }

  function deleteSlide(index: number) {
    slides = slides.filter((_, i) => i !== index);
  }

  function validateSlides(): string | undefined {
    for (let i = 0; i < slides.length; i++) {
      const slide = slides[i];
      const hasContent = slide.text || slide.answer;
      const hasMedia = slide.media_type && slide.media_url;

      if (!hasContent && !hasMedia) {
        return `Slide ${i + 1} must have text, answer, or media`;
      }

      if ((slide.media_type && !slide.media_url) || (!slide.media_type && slide.media_url)) {
        return `Slide ${i + 1}: media_type and media_url must be set together`;
      }
    }
    return undefined;
  }

  async function handleSave() {
    const validationError = validateSlides();
    if (validationError) {
      error = validationError;
      return;
    }

    saving = true;
    error = undefined;

    try {
      const updates: QuestionUpdateRequest = {
        text,
        answer,
        points,
        slides,
      };
      await updateQuestion(questionId, updates);
      await goto(`/${gameId}/host`);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to save question';
      saving = false;
    }
  }

  function handleCancel() {
    goto(`/${gameId}/host`);
  }
</script>

<div class="min-h-screen bg-surface-900 p-8 text-surface-50">
  <div class="mx-auto max-w-4xl">
    <div class="mb-6 flex items-center justify-between">
      <h1 class="text-3xl font-bold">Edit Question</h1>
      <button class="btn-variant-ghost btn" onclick={handleCancel}>✕</button>
    </div>

    {#if loading}
      <p class="text-center text-primary-400">Loading question...</p>
    {:else if error}
      <p class="mb-4 text-error-400">{error}</p>
    {/if}

    {#if !loading}
      <div class="space-y-6">
        <div class="space-y-4 rounded-lg border border-surface-600 bg-surface-800 p-6">
          <h2 class="text-xl font-semibold">Question Metadata</h2>

          <label class="block">
            <span class="mb-1 block font-semibold">Question Text</span>
            <textarea bind:value={text} class="textarea w-full" rows="3"></textarea>
          </label>

          <div class="grid grid-cols-2 gap-4">
            <label class="block">
              <span class="mb-1 block font-semibold">Overall Answer</span>
              <input type="text" bind:value={answer} class="input w-full" />
            </label>

            <label class="block">
              <span class="mb-1 block font-semibold">Points</span>
              <input type="number" bind:value={points} class="input w-full" min="0" />
            </label>
          </div>
        </div>

        <div class="space-y-4 rounded-lg border border-surface-600 bg-surface-800 p-6">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-semibold">
              Slides {slides.length > 0 ? `(${slides.length})` : ''}
            </h2>
            <button class="btn-variant-filled btn" onclick={addSlide}>+ Add Slide</button>
          </div>

          {#if slides.length === 0}
            <p class="text-sm text-primary-400">
              No slides yet. Click "Add Slide" to create a multi-slide question.
            </p>
          {:else}
            <div class="space-y-4">
              {#each slides as slide, index}
                <div>
                  <p class="mb-2 text-sm text-primary-300">Slide {index + 1}</p>
                  <SlideEditor
                    {slide}
                    onChange={(s) => updateSlide(index, s)}
                    onDelete={() => deleteSlide(index)}
                  />
                </div>
              {/each}
            </div>
          {/if}
        </div>

        <div class="flex justify-end gap-2 border-t border-surface-600 pt-4">
          <button class="btn-variant-ghost btn" onclick={handleCancel} disabled={saving}>
            Cancel
          </button>
          <button class="btn-variant-filled btn" onclick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>
