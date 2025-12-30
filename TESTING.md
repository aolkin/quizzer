# Testing Strategy

## Philosophy

Focus on **high-value tests** that verify interesting logic and prevent regressions. Avoid bloating the codebase with redundant or trivial tests.

This philosophy applies to both frontend (TypeScript/Svelte) and backend (Python/Django) code.

## What to Test

### ✅ High-Value Tests

- **Complex logic**: Race condition prevention, version tracking, state management
- **Critical paths**: WebSocket message handling, state updates, API endpoints
- **Integration points**: API calls with proper error handling, database operations
- **Edge cases**: Out-of-order updates, reconnection logic, error conditions
- **Business logic**: Score calculations, game state transitions, validation rules
- **Multi-client sync**: Real-time updates across host and presenter clients

### ❌ Low-Value Tests (Avoid)

- **Trivial setters/getters**: Simple one-line functions
- **Configuration/environment**: URL formatting, constant values
- **Redundant coverage**: Testing the same logic multiple times
- **Framework behavior**: Testing library/framework features
- **Simple CRUD**: Basic database operations without complex logic

## Guidelines

1. **Consolidate overlapping tests**: If logic is shared (e.g., `shouldUpdatePlayer` and `shouldUpdateQuestion`), test it once
2. **Prefer property-based or parameterized testing** for exhaustive input coverage
3. **Focus on behavior, not implementation**: Test what the code does, not how it does it
4. **Keep tests readable**: Clear names, minimal setup, obvious assertions
5. **Mock external dependencies**: Use mocks for WebSocket, fetch, database, etc. (in unit tests)
6. **Use E2E tests for integration**: Test real WebSocket and API interactions with Playwright

## Examples

### Frontend (TypeScript/Svelte)

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

### Backend (Python/Django)

❌ **Bad**: Testing trivial model properties

```python
def test_team_name(self):
    team = Team(name="Red Team")
    self.assertEqual(team.name, "Red Team")
```

✅ **Good**: Testing complex business logic

```python
def test_score_calculation_with_daily_double(self):
    """Test that Daily Double correctly multiplies the wager"""
    game = create_test_game()
    player = create_test_player(score=500)
    question = create_daily_double(value=400)

    answer_question(player, question, correct=True, wager=500)

    self.assertEqual(player.score, 1000)  # 500 + 500 wager
```

## Running Tests

### Frontend Unit Tests
```bash
bun run test          # Run all tests once
bun run test:unit     # Run tests in watch mode
```

### Frontend E2E Tests (Playwright)
```bash
cd app
npm run test:e2e        # Run E2E tests
npm run test:e2e:ui     # Run with interactive UI
npm run test:e2e:debug  # Run in debug mode
```

E2E tests automatically start the Django backend and Vite dev server.
See `app/tests/e2e/README.md` for detailed documentation.

### Backend
```bash
python manage.py test                    # Run all tests
python manage.py test game.tests         # Run specific app tests
coverage run --source='.' manage.py test # Run with coverage
coverage report                          # Show coverage report
```

## E2E Testing with Playwright

E2E tests verify the full stack including WebSocket synchronization and multi-client scenarios.

### Key E2E Test Scenarios

1. **Multi-client sync**: Host actions propagate to presenter clients
2. **WebSocket relay**: Board selection, category reveal, question presentation
3. **Score updates**: Points awarded via REST API broadcast to all clients
4. **Buzzer system**: Enable/disable buzzers, buzzer press handling

### Test Data

Test games are loaded via the import API from `service/fixtures/test_game.json`.
