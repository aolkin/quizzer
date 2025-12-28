# Fix Frontend CI Type Checking and Linting

## Issue
Frontend CI steps for type checking (svelte-check) and linting (eslint) are currently failing and have been temporarily disabled in the CI workflow.

## Current State
- **Type Checking (svelte-check)**: Disabled in CI - 12 TypeScript errors and 4 warnings across 7 files
- **Linting (eslint)**: Disabled in CI - Multiple linting errors
- **Tests**: ✅ Working (16 tests passing)
- **Build**: ✅ Working (builds successfully)

## Type Check Errors (12 errors, 4 warnings)

### TypeScript Errors
1. `src/routes/[game]/[[mode]]/+page.ts:9:3` - Member 'fetch' implicitly has 'any' type
2. `src/lib/audio.svelte.ts:14:11` - Property 'websocket' has no initializer
3. `src/lib/websocket.ts:20:11` - Property 'socket' has no initializer
4. `src/lib/websocket.ts:65:17` - Parameter 'event' implicitly has 'any' type
5. `src/lib/websocket.ts:116:18` - Parameter 'categoryId' implicitly has 'any' type
6. `src/lib/websocket.ts:123:15` - Parameter 'board' implicitly has 'any' type
7. `src/lib/websocket.ts:130:18` - Parameter 'question' implicitly has 'any' type
8. `src/lib/components/QuestionDisplay.svelte:14:26` - 'container.parentElement' is possibly 'null'
9. `src/lib/components/Board.svelte:66:44` - Property 'status' does not exist on type 'Question'
10. `src/lib/components/ScoreFooter.svelte:32:53` - Right operand of ?? is unreachable
11. `src/routes/[game]/[[mode]]/+page.svelte:26:46` - Type 'string | undefined' not assignable
12. `src/routes/[game]/[[mode]]/+page.svelte:39:43` - Type 'AudioClient | undefined' not assignable

### Svelte Warnings
1. `QuestionDisplay.svelte:62:9` - `<video>` elements must have `<track kind="captions">`
2. `QuestionDisplay.svelte:62:9` - Self-closing HTML tags for non-void elements (video)
3. `QuestionDisplay.svelte:64:9` - Self-closing HTML tags for non-void elements (audio)
4. `QuestionDisplay.svelte:10:7` - `questionText` not declared with `$state(...)`

## ESLint Errors
Multiple linting errors across the codebase (exact count TBD).

## Action Items

### High Priority
- [ ] Fix TypeScript strict type checking errors
  - [ ] Add proper type annotations for 'any' types
  - [ ] Initialize class properties or mark as optional
  - [ ] Add null checks where needed
  - [ ] Fix type mismatches for optional parameters

### Medium Priority
- [ ] Fix Svelte warnings
  - [ ] Add captions track to video elements
  - [ ] Fix self-closing tags for video/audio elements
  - [ ] Use `$state()` for reactive variables

### Lower Priority
- [ ] Fix ESLint errors
  - [ ] Run `bun run lint` and address reported issues
  - [ ] Consider updating ESLint rules if too strict

### CI Re-enablement
- [ ] Once fixes are complete, re-enable type checking in `.github/workflows/frontend-ci.yml`
- [ ] Once fixes are complete, re-enable linting in `.github/workflows/frontend-ci.yml`

## Why This Matters
- **Type Safety**: TypeScript errors can lead to runtime bugs
- **Accessibility**: Missing captions on video elements affects accessibility
- **Code Quality**: Linting ensures consistent code style
- **CI/CD**: Automated checks catch issues before code review

## Timeline
Should be addressed before major feature development to prevent technical debt accumulation.
