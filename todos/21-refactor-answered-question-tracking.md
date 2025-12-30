# Refactor Frontend Answered Question Tracking

## Problem

The frontend currently has two sources of truth for tracking which questions have been answered:

1. **`question.answered`** - Boolean property on each Question object from the initial API response
2. **`gameState.answeredQuestions`** - A reactive SvelteSet that gets updated via WebSocket broadcasts

This creates several issues:

### Current Workarounds
- Board.svelte was changed to use `gameState.answeredQuestions.has(question.id)` instead of `question.answered` for the opacity class
- When loading a board, we extract `answered` flags from questions and populate the Set
- The original `question.answered` properties are never updated, creating stale data

### Potential Bugs
- If any component still reads `question.answered` directly, it won't see real-time updates
- The `question.answered` property becomes stale after any toggle operation
- Two different representations of the same data can drift apart

## Proposed Solution

### Option A: Single Source of Truth in gameState (Recommended)
- Keep only `gameState.answeredQuestions` SvelteSet
- Remove reliance on `question.answered` property entirely
- Populate the Set when board data is loaded
- All components read from the Set

**Pros**: Clean separation, clear single source of truth
**Cons**: Slight indirection when checking if a question is answered

### Implementation Plan

1. [ ] Audit all usages of `question.answered` in components
2. [ ] Replace all with `gameState.answeredQuestions.has(question.id)` 
3. [ ] Add a helper method: `gameState.isQuestionAnswered(questionId): boolean`
4. [ ] Update TypeScript types to make `question.answered` optional or internal-only
5. [ ] Update API response handling to only use `answered` for initial population
6. [ ] Document the convention: "WebSocket state (gameState.*) is the source of truth for UI"

## Where State is Used

Currently `question.answered` is used:
- **On initial load**: Extract from API response to populate `gameState.answeredQuestions`
- **During sync**: WebSocket `toggle_question` messages update `gameState.answeredQuestions` directly

The convention going forward should be:
- API responses provide initial state
- WebSocket messages provide real-time updates to reactive state
- UI always reads from reactive state (gameState.*)

## Related Pattern: gameState.scores

Note: `gameState.scores` follows the same pattern - player scores are tracked separately from Player objects. This is intentional and allows real-time score updates without mutating nested objects. The same approach works well for answered questions.

## Related Files

- `app/src/lib/game-state.svelte.ts` - State management
- `app/src/lib/components/Board.svelte` - Uses answered state for UI
- `app/src/lib/websocket.ts` - Handles toggle_question messages
- `app/src/lib/state.svelte.ts` - Question type definition

## Priority

**Low** - The current implementation works correctly after the E2E testing fixes. This is a code quality improvement to reduce technical debt.
