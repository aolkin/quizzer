# Quizzer Frontend

SvelteKit frontend application for the Quizzer interactive Jeopardy game system.

## Developing

Once you've created a project and installed dependencies with `bun install`, start a development server:

```bash
bun run dev

# or start the server and open the app in a new browser tab
bun run dev -- --open
```

## Building

To create a production version of your app:

```bash
bun run build
```

You can preview the production build with `bun run preview`.

## Quality Checks

Before committing changes, run:

```bash
bun run lint    # Linting and formatting
bun run check   # Type checking
bun run test    # Run tests
bun run build   # Build verification
```

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.
