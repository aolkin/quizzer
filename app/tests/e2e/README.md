# End-to-End Tests

This directory contains Playwright E2E tests for the Quizzer application.

## Test Architecture

The E2E tests run against a real Django backend and test the full stack including:

- WebSocket relay and synchronization
- REST API endpoints
- Multi-client scenarios (host + presenter)
- Browser interactions

## Running Tests

### Prerequisites

1. Install dependencies:

   ```bash
   cd app
   npm install
   npx playwright install chromium
   ```

2. Ensure the backend dependencies are installed:
   ```bash
   cd service
   pip install -r requirements.lock
   ```

### Running Tests Locally

```bash
cd app

# Run all E2E tests
npm run test:e2e

# Run tests with UI mode (interactive debugging)
npm run test:e2e:ui

# Run tests in debug mode
npm run test:e2e:debug

# Run a specific test file
npx playwright test tests/e2e/host-basic.spec.ts
```

The test runner will automatically start:

- Django backend on port 8000
- Vite dev server on port 5173

### Test Files

| File                        | Description                            |
| --------------------------- | -------------------------------------- |
| `host-basic.spec.ts`        | Basic host mode operations             |
| `presenter-basic.spec.ts`   | Presentation mode verification         |
| `multi-client-sync.spec.ts` | Multi-client WebSocket synchronization |
| `buzzer.spec.ts`            | Buzzer system functionality            |
| `error-handling.spec.ts`    | Error scenarios and edge cases         |

### Setup Files

| File                       | Description                                          |
| -------------------------- | ---------------------------------------------------- |
| `setup/fixtures.ts`        | Custom test fixtures for multi-client contexts       |
| `setup/global-setup.ts`    | Global setup - waits for backend and loads test data |
| `setup/global-teardown.ts` | Global teardown - cleanup after tests                |

## Writing New Tests

### Basic Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    const gameId = process.env.TEST_GAME_ID || '1';
    await page.goto(`/${gameId}/host`);
    await page.waitForLoadState('networkidle');
  });

  test('does something', async ({ page }) => {
    await expect(page.locator('[data-testid="some-element"]')).toBeVisible();
  });
});
```

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

Test data is loaded from `service/fixtures/test_game.json` via the import API during global setup.

The test game includes:

- 2 boards (Round 1, Round 2)
- Multiple categories per board
- Questions of various point values
- 2 teams with 2 players each

## Debugging Failed Tests

1. **View HTML Report**:

   ```bash
   npx playwright show-report
   ```

2. **Run in Debug Mode**:

   ```bash
   npm run test:e2e:debug
   ```

3. **Check Screenshots**: Failed tests save screenshots to `test-results/`

4. **View Traces**: Traces are recorded on first retry and can be viewed with:
   ```bash
   npx playwright show-trace test-results/path-to-trace.zip
   ```

## CI Integration

E2E tests run in GitHub Actions CI as a separate job in parallel with unit tests.
The workflow:

1. Sets up Python and Node.js
2. Installs dependencies
3. Starts Django backend
4. Loads test game data
5. Runs Playwright tests
6. Uploads artifacts on failure
