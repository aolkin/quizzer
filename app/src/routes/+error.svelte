<script lang="ts">
  import { page } from '$app/stores';
</script>

<div class="flex min-h-screen items-center justify-center bg-surface-900 text-surface-50">
  <div class="error-container text-center">
    <h1 class="mb-4 text-6xl font-bold">{$page.status}</h1>
    <p class="mb-8 text-2xl">{$page.error?.message || 'An error occurred'}</p>
    <a href="/" class="text-primary-500 underline hover:text-primary-400"> Return to home </a>
  </div>
</div>
