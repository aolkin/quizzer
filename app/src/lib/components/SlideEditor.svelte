<script lang="ts">
  import type { Slide } from '$lib/state.svelte';
  import type { MediaFile } from '$lib/api';
  import MediaBrowser from './MediaBrowser.svelte';

  let {
    slide,
    onChange,
    onDelete,
  }: {
    slide: Slide;
    onChange: (slide: Slide) => void;
    onDelete: () => void;
  } = $props();

  let localSlide = $state<Slide>({});
  let showMediaBrowser = $state(false);

  $effect(() => {
    localSlide = { ...slide };
  });

  $effect(() => {
    onChange(localSlide);
  });

  function handleMediaSelect(file: MediaFile) {
    const mediaType = detectMediaType(file.original_filename);
    localSlide = { ...localSlide, media_type: mediaType, media_url: file.url };
    showMediaBrowser = false;
  }

  function clearMedia() {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { media_type, media_url, ...rest } = localSlide;
    localSlide = rest;
  }

  function detectMediaType(filename: string): 'image' | 'video' | 'audio' {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext || '')) return 'image';
    if (['mp4', 'webm', 'mov', 'avi'].includes(ext || '')) return 'video';
    return 'audio';
  }
</script>

<div class="space-y-3 rounded-lg border border-surface-600 bg-surface-700 p-4">
  <div class="flex items-center justify-between">
    <h4 class="font-semibold">Slide Content</h4>
    <button class="btn-variant-ghost btn btn-sm text-error-400" onclick={onDelete}>
      Delete Slide
    </button>
  </div>

  <label class="block">
    <span class="mb-1 block text-sm">Text (optional)</span>
    <textarea
      bind:value={localSlide.text}
      class="textarea w-full"
      rows="2"
      placeholder="Slide text..."
    ></textarea>
  </label>

  <div>
    <span class="mb-2 block text-sm">Media (optional)</span>
    {#if localSlide.media_url && localSlide.media_type}
      <div class="mb-2 rounded border border-surface-600 bg-surface-800 p-2">
        {#if localSlide.media_type === 'image'}
          <img src={localSlide.media_url} alt="Preview" class="max-h-32 rounded" />
        {:else}
          <p class="text-sm">{localSlide.media_type}: {localSlide.media_url}</p>
        {/if}
        <button class="btn-variant-ghost btn btn-sm mt-2" onclick={clearMedia}>
          Remove Media
        </button>
      </div>
    {/if}
    <button class="btn-variant-ringed btn btn-sm" onclick={() => (showMediaBrowser = true)}>
      Browse Media
    </button>
  </div>

  <label class="block">
    <span class="mb-1 block text-sm">Slide Answer (optional)</span>
    <input
      type="text"
      bind:value={localSlide.answer}
      class="input w-full"
      placeholder="Answer for this slide..."
    />
  </label>
</div>

<MediaBrowser
  open={showMediaBrowser}
  onSelect={handleMediaSelect}
  onClose={() => (showMediaBrowser = false)}
/>
