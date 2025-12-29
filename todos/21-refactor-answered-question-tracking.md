# Refactor Frontend Answered Question Tracking

## Problem

The frontend currently has two sources of truth for tracking which questions have been answered:

1. **`question.answered`** - Boolean property on each Question object from the initial API response
2. **`gameState.answeredQuestions`** - A reactive Set that gets updated via WebSocket broadcasts

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

### Option A: Single Source of Truth in gameState
- Keep only `gameState.answeredQuestions` Set
- Remove reliance on `question.answered` property entirely
- Populate the Set when board data is loaded
- All components read from the Set

**Pros**: Clean separation, clear single source of truth
**Cons**: Slight indirection when checking if a question is answered

### Option B: Update question.answered Directly
- When receiving `toggle_question` WebSocket message, find and update the actual Question object
- Remove `answeredQuestions` Set entirely

**Pros**: Simpler data model, question objects are always current
**Cons**: Requires finding question in nested board/category structure, may have reactivity issues with nested object mutations

### Option C: Hybrid with Computed State
- Keep the Set for efficient lookups
- Create a helper function/computed that checks both sources
- Ensure consistency when loading boards

## Recommendation

**Option A** is likely the cleanest approach and aligns with the pattern already established:
- `gameState.scores` tracks player scores separately from Player objects
- `gameState.answeredQuestions` follows the same pattern

## Implementation Steps

1. [ ] Audit all usages of `question.answered` in components
2. [ ] Replace all with `gameState.answeredQuestions.has(question.id)`
3. [ ] Consider adding a helper method: `gameState.isQuestionAnswered(questionId)`
4. [ ] Update TypeScript types to make `question.answered` optional or remove it
5. [ ] Update tests to verify the new approach

## Related Files

- `app/src/lib/game-state.svelte.ts` - State management
- `app/src/lib/components/Board.svelte` - Uses answered state for UI
- `app/src/lib/websocket.ts` - Handles toggle_question messages
- `app/src/lib/state.svelte.ts` - Question type definition

## Priority

**Low** - The current implementation works correctly after the E2E testing fixes. This is a code quality improvement to reduce technical debt.
