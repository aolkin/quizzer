import { skeleton } from '@skeletonlabs/tw-plugin';
import { join } from 'path';
import forms from '@tailwindcss/forms';
import type { Config } from 'tailwindcss';

export default {
  darkMode: 'class',
  content: [
    './src/**/*.{html,js,svelte,ts}',
    join(require.resolve('@skeletonlabs/skeleton'), '../**/*.{html,js,svelte,ts}'),
  ],

  theme: {
    extend: {},
  },

  plugins: [
    forms,
    skeleton({
      themes: { preset: ['skeleton', 'modern', 'crimson', 'rocket', 'hamlindigo', 'seafoam'] },
    }),
  ],
} satisfies Config;
