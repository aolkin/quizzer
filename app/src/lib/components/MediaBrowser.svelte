<script lang="ts">
  import { onMount } from 'svelte';
  import Icon from '@iconify/svelte';
  import { listMedia, type MediaFile } from '$lib/api';

  let {
    open,
    onSelect,
    onClose,
  }: {
    open: boolean;
    onSelect: (file: MediaFile) => void;
    onClose: () => void;
  } = $props();

  let media = $state<MediaFile[]>([]);
  let loading = $state(true);
  let error = $state<string | undefined>(undefined);
  let searchQuery = $state('');

  const filteredMedia = $derived(
    media.filter((m) => m.original_filename.toLowerCase().includes(searchQuery.toLowerCase())),
  );

  onMount(async () => {
    await loadMedia();
  });

  async function loadMedia() {
    loading = true;
    error = undefined;
    try {
      media = await listMedia();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load media files';
    } finally {
      loading = false;
    }
  }

  function handleSelect(file: MediaFile) {
    onSelect(file);
  }

  function getMediaType(filename: string): 'image' | 'video' | 'audio' | 'unknown' {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext || '')) return 'image';
    if (['mp4', 'webm', 'mov', 'avi'].includes(ext || '')) return 'video';
    if (['mp3', 'wav', 'ogg', 'm4a'].includes(ext || '')) return 'audio';
    return 'unknown';
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }
</script>

{#if open}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    onclick={onClose}
    onkeydown={(e) => e.key === 'Escape' && onClose()}
    role="presentation"
  >
    <div
      class="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-lg bg-surface-800 p-6"
      onclick={(e) => e.stopPropagation()}
      onkeydown={(e) => e.stopPropagation()}
      role="dialog"
      aria-modal="true"
      aria-labelledby="media-browser-title"
      tabindex="-1"
    >
      <div class="mb-4 flex items-center justify-between">
        <h2 id="media-browser-title" class="text-2xl font-bold">Browse Media</h2>
        <button class="btn-variant-ghost btn" onclick={onClose} aria-label="Close media browser">
          ✕
        </button>
      </div>

      <input
        type="text"
        bind:value={searchQuery}
        placeholder="Search files..."
        class="input mb-4 w-full"
      />

      {#if loading}
        <p class="text-center text-primary-400">Loading media...</p>
      {:else if error}
        <p class="text-center text-error-400">{error}</p>
      {:else if filteredMedia.length === 0}
        <div class="text-center text-primary-400">
          <p class="mb-2">No media files found.</p>
          <p class="text-sm">
            Upload files via <a href="/admin/game/mediafile/" class="underline">Django admin</a>
          </p>
        </div>
      {:else}
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {#each filteredMedia as file}
            <button
              class="overflow-hidden rounded-lg border border-surface-600 bg-surface-700 text-left transition-colors hover:border-primary-400 hover:bg-surface-600"
              onclick={() => handleSelect(file)}
            >
              <div class="flex aspect-video items-center justify-center bg-surface-900">
                {#if getMediaType(file.original_filename) === 'image'}
                  <img
                    src={file.url}
                    alt={file.original_filename}
                    class="h-full w-full object-cover"
                  />
                {:else}
                  <Icon
                    icon="mdi:{getMediaType(file.original_filename)}"
                    class="text-6xl text-primary-400"
                  />
                {/if}
              </div>

              <div class="p-3">
                <p class="truncate text-sm font-medium" title={file.original_filename}>
                  {file.original_filename}
                </p>
                <p class="text-xs text-primary-400">
                  {formatFileSize(file.file_size)} • {formatDate(file.uploaded_at)}
                </p>
              </div>
            </button>
          {/each}
        </div>
      {/if}
    </div>
  </div>
{/if}
