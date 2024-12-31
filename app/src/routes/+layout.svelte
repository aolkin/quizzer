<script lang="ts">
  import '../app.css';
	import { initializeStores } from '@skeletonlabs/skeleton';

	initializeStores();

  let { children } = $props();
</script>

{@render children()}
