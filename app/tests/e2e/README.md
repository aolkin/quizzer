# End-to-End Tests

Playwright E2E tests for the Quizzer application, testing the full stack including WebSocket synchronization and multi-client scenarios.

## Running Tests

### Local Development

Start the Django backend and Vite dev server before running tests:

```bash
# Terminal 1: Start backend
cd service
uv run python manage.py runserver 8000

# Terminal 2: Start frontend
cd app
VITE_API_ENDPOINT=localhost:8000 bun run dev
```

Then run tests:

```bash
cd app

# Run all E2E tests
bun run test:e2e

# Run with UI mode (interactive debugging)
bun run test:e2e:ui

# Run in debug mode
bun run test:e2e:debug
```

### CI

In CI (`CI=true`), Playwright automatically starts both servers using the `webServer` config. No manual server startup is needed.

## Writing Tests

### Multi-Client Test Pattern

```typescript
test('host action syncs to presenter', async ({ browser }) => {
  const hostContext = await browser.newContext();
  const presenterContext = await browser.newContext();

  const hostPage = await hostContext.newPage();
  const presenterPage = await presenterContext.newPage();

  const gameId = process.env.TEST_GAME_ID || '1';

  await Promise.all([
    hostPage.goto(`/${gameId}/host`),
    presenterPage.goto(`/${gameId}/presentation`),
  ]);

  // Perform action on host
  await hostPage.click('[data-testid="some-button"]');

  // Verify sync to presenter
  await expect(presenterPage.locator('[data-testid="some-result"]')).toBeVisible();

  await hostContext.close();
  await presenterContext.close();
});
```

## Test Data

Test data is loaded from `fixtures/test_game.json` via the import API during global setup.

## Debugging

- **HTML Report**: `bunx playwright show-report`
- **Screenshots**: Failed tests save screenshots to `test-results/`
- **Traces**: `bunx playwright show-trace test-results/path-to-trace.zip`
