# Frontend State Management Issues

## Issue
Mixed use of Svelte 5 runes and Svelte 4 stores causing confusion.

## Problems

### 1. Dual State Systems
- `lib/stores.ts`: Uses Svelte 4 writable stores
- `+page.svelte`: Uses Svelte 5 `$state()` runes
- Both active simultaneously

### 2. WebSocket Stored Twice
- Local variable in `+page.svelte:17`
- Also stored in `gameState.websocket` (line 25)
- Unclear which is source of truth

### 3. Inconsistent Send Methods (`websocket.ts`)
Lines 158-164 vs other methods:
```typescript
// Some methods use this.send()
selectBoard(board) {
    this.send({ type: 'select_board', board });
}

// Others use this.socket.send() directly
recordPlayerAnswer(...) {
    this.socket.send(JSON.stringify({...})); // Different pattern!
}
```

### 4. Direct Store Mutations
`websocket.ts` directly calls `gameState.update()` in multiple places, violating separation of concerns.

## Proposed Solution

### Option A: Full Svelte 5 Migration
- Convert stores to runes-based state
- Use `$derived` for computed values
- Keep WebSocket separate from reactive state

### Option B: Keep Stores, Remove Runes
- Stick with Svelte stores
- Remove `$state` from components
- Standardize on stores pattern

## Recommendation
Go with Option A since the app is already using Svelte 5 features.

## Action Items
- [ ] Choose migration strategy
- [ ] Consolidate WebSocket send methods to use `this.send()`
- [ ] Remove duplicate WebSocket storage
- [ ] Create state management utilities/hooks
- [ ] Document state management pattern
