# End-to-End Tests

Playwright E2E tests for the Quizzer application, testing the full stack including WebSocket synchronization and multi-client scenarios.

## Running Tests

```bash
cd app

# Run all E2E tests
npm run test:e2e

# Run with UI mode (interactive debugging)
npm run test:e2e:ui

# Run in debug mode
npm run test:e2e:debug
```

The test runner automatically starts the Django backend and Vite dev server.

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

- **HTML Report**: `npx playwright show-report`
- **Screenshots**: Failed tests save screenshots to `test-results/`
- **Traces**: `npx playwright show-trace test-results/path-to-trace.zip`
