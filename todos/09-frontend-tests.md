# Frontend Test Coverage

## Issue
No frontend test coverage despite Vitest being configured.

## Current State
- Vitest configured in `package.json`
- Only `demo.spec.ts` exists (likely boilerplate)
- No component tests
- No WebSocket client tests
- No state management tests
- No version tracking tests

## Why This Matters
- WebSocket reconnection logic is complex
- Version number handling prevents race conditions (needs verification)
- State management is mixed (Svelte 4/5) and needs validation
- Score updates from multiple sources need testing

## Priority Areas

### 1. Version Tracking (Highest Priority)
Test the race condition prevention:
```typescript
describe('Version tracking', () => {
  it('ignores out-of-order score updates', () => {
    handleScoreUpdate(1, 400, 42);  // version 42
    handleScoreUpdate(1, 200, 41);  // older version - should ignore
    expect(getPlayerScore(1)).toBe(400);
  });

  it('accepts newer versions', () => {
    handleScoreUpdate(1, 400, 42);
    handleScoreUpdate(1, 600, 43);  // newer version - should apply
    expect(getPlayerScore(1)).toBe(600);
  });
});
```

### 2. WebSocket Client Tests
```typescript
describe('GameWebSocket', () => {
  it('handles score update messages', () => {
    // Test message parsing and state updates
  });

  it('reconnects on disconnect', () => {
    // Test exponential backoff
  });

  it('sends coordination messages via relay', () => {
    // Test select_question, reveal_category
  });

  it('calls REST API for mutations', () => {
    // Test record_answer uses fetch, not WebSocket
  });
});
```

### 3. State Management Tests
```typescript
describe('Game state', () => {
  it('updates from WebSocket broadcasts', () => {
    // Test gameState reactivity
  });

  it('tracks answered questions', () => {
    // Test Set operations
  });

  it('handles board switching', () => {
    // Test state reset on board change
  });
});
```

### 4. Component Tests
```typescript
describe('Board component', () => {
  it('renders all categories', () => {});

  it('grays out answered questions', () => {});

  it('handles question selection', () => {});
});

describe('ScoreFooter', () => {
  it('displays all team scores', () => {});

  it('updates when scores change', () => {});
});
```

### 5. API Integration Tests
```typescript
describe('REST API calls', () => {
  it('records answer and returns version', async () => {
    const response = await recordAnswer(1, 1, true);
    expect(response.version).toBeGreaterThan(0);
    expect(response.score).toBeDefined();
  });

  it('handles 404 errors gracefully', async () => {
    // Test error handling
  });
});
```

## Test Organization
```
app/src/
├── lib/
│   ├── websocket.test.ts
│   ├── state.test.ts
│   ├── audio.test.ts
│   └── components/
│       ├── Board.test.ts
│       ├── ScoreFooter.test.ts
│       └── QuestionDisplay.test.ts
```

## Action Items
- [ ] Remove demo.spec.ts boilerplate
- [ ] Write version tracking tests (critical for race condition prevention)
- [ ] Write WebSocket client tests
- [ ] Write state management tests
- [ ] Write component rendering tests
- [ ] Add API error handling tests
- [ ] Mock WebSocket server for integration tests
- [ ] Add coverage reporting

## Tools & Frameworks
- Vitest (already configured)
- @testing-library/svelte for component tests
- Mock WebSocket server for integration tests
- Coverage with Vitest

## Success Criteria
- Version tracking has 100% coverage (critical for correctness)
- WebSocket client message handlers are tested
- Components render without errors
- State updates are verified
- CI runs tests on every commit
