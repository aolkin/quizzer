# Testing Strategy

## Philosophy

Focus on **high-value tests** that verify interesting logic and prevent regressions. Avoid bloating the codebase with redundant or trivial tests.

## What to Test

### ✅ High-Value Tests

- **Complex logic**: Race condition prevention, version tracking
- **Critical paths**: WebSocket message handling, state updates
- **Integration points**: API calls with proper error handling
- **Edge cases**: Out-of-order updates, reconnection logic

### ❌ Low-Value Tests (Avoid)

- **Trivial setters/getters**: Simple one-line functions
- **Configuration/environment**: URL formatting, constant values
- **Redundant coverage**: Testing the same logic multiple times
- **Framework behavior**: Testing library/framework features

## Guidelines

1. **Consolidate overlapping tests**: If logic is shared (e.g., `shouldUpdatePlayer` and `shouldUpdateQuestion`), test it once
2. **Prefer property-based or parameterized testing** for exhaustive input coverage
3. **Focus on behavior, not implementation**: Test what the code does, not how it does it
4. **Keep tests readable**: Clear names, minimal setup, obvious assertions
5. **Mock external dependencies**: Use mocks for WebSocket, fetch, etc.

## Example

❌ **Bad**: Testing every variation of a simple setter

```typescript
it('sets score to 100', () => {
  /* ... */
});
it('sets score to 200', () => {
  /* ... */
});
it('sets score to 300', () => {
  /* ... */
});
```

✅ **Good**: Testing the interesting behavior

```typescript
it('prevents out-of-order updates for race condition safety', () => {
  shouldUpdatePlayer(1, 42);
  expect(shouldUpdatePlayer(1, 41)).toBe(false); // Reject older
  expect(shouldUpdatePlayer(1, 43)).toBe(true); // Accept newer
});
```

## Running Tests

```bash
npm test              # Run all tests once
npm run test:unit     # Run tests in watch mode
```
