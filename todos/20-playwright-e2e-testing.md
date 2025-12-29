# Playwright E2E Testing for Frontend

## Problem

Currently, the frontend only has unit tests (Vitest) that mock WebSocket connections and API calls. While these tests verify isolated component logic, they don't catch:
- Integration bugs between frontend and backend
- Real WebSocket relay behavior (multi-client synchronization)
- Race conditions in concurrent updates
- Full user workflows (host controls → presenter updates)
- Cross-browser compatibility issues
- Real network reconnection scenarios

## Proposed Solution

Implement end-to-end testing using Playwright that runs against a real Django backend, testing the full stack including WebSocket relay, API endpoints, and multi-client scenarios.

### Key Features

1. **Real Backend Integration**
   - Django dev server running during tests
   - SQLite test database with seeded game data
   - Real WebSocket connections through Django Channels
   - Actual API endpoints (no mocking)

2. **Multi-Client Testing**
   - Simultaneous host + presenter(s) contexts
   - Test real-time synchronization via WebSocket relay
   - Verify state updates propagate correctly
   - Test buzzer competition between multiple clients

3. **Chrome-Only Testing**
   - Chromium browser only (cost optimization)
   - Covers vast majority of real-world usage
   - Can expand to Firefox/Safari later if needed

4. **Test Scenarios Aligned with Testing Philosophy**
   - Focus on high-value integration tests
   - Complex multi-client workflows
   - WebSocket reconnection and recovery
   - Race condition handling (version conflicts)
   - Critical user paths (not trivial interactions)

## Test Game Data Strategy

Use the **import/export API** (TODO #19) to load test game data:

- Commit JSON game export file (`service/fixtures/test_game.json`)
- Contains 1-2 pre-configured games with boards, questions, teams
- Load via import API in global setup before tests
- Human-readable, version-controlled, easy to modify
- Validates import/export functionality as bonus

## Implementation Steps

### Phase 1: Setup & Configuration
- [ ] Install Playwright: `cd app && bun add -D @playwright/test`
- [ ] Initialize Playwright config: `bunx playwright install`
- [ ] Create `app/playwright.config.ts` with:
  - Base URL pointing to `http://localhost:5173` (Vite dev server)
  - API URL pointing to `http://localhost:8000` (Django backend)
  - Browser projects: chromium only (cost optimization)
  - Parallel workers for speed (2-4 workers)
  - Screenshot/video on failure
  - Headless mode for CI
- [ ] Add npm scripts to `app/package.json`:
  - `"test:e2e": "playwright test"`
  - `"test:e2e:ui": "playwright test --ui"`
  - `"test:e2e:debug": "playwright test --debug"`
- [ ] Create `app/tests/e2e/` directory for test files
- [ ] Add Playwright to `.gitignore`: `test-results/`, `playwright-report/`

### Phase 2: Test Infrastructure
- [ ] Create `app/tests/e2e/setup/` directory for test helpers
- [ ] Create **backend manager** (`backend-manager.ts`):
  - Function to start Django dev server (`python manage.py runserver 8000`)
  - Function to stop server on teardown
  - Check if server is already running (avoid conflicts)
  - Wait for server health check before tests
- [ ] Create **database manager** (`database-manager.ts`):
  - Load test game via import API (POST /api/import/)
  - Use fixture file `service/fixtures/test_game.json`
  - Reset database between test runs (Django migrations)
  - Store game ID for test access
- [ ] Create **test fixtures** (`fixtures.ts`):
  - Custom fixture for multi-client contexts (host + presenters)
  - Fixture for pre-authenticated pages
  - Fixture for game URL navigation
- [ ] Create **global setup** (`playwright/global-setup.ts`):
  - Start backend server in background
  - Run Django migrations (fresh test DB)
  - Load test game via import API
  - Verify backend is healthy (health check endpoint)
  - Store test game ID in environment variable
- [ ] Create **global teardown** (`playwright/global-teardown.ts`):
  - Stop backend server
  - Clean up test database

### Phase 3: Core Test Suites

#### Suite 1: Single Client - Host Mode
- [ ] `app/tests/e2e/host-basic.spec.ts`:
  - Load game page in host mode
  - Select a board
  - Reveal categories one by one
  - Select a question (verify full-screen display)
  - Mark question as answered
  - Award/deduct points to players
  - Verify score updates persist (reload page, check score)

#### Suite 2: Single Client - Presentation Mode
- [ ] `app/tests/e2e/presenter-basic.spec.ts`:
  - Load game page in presentation mode
  - Verify read-only behavior (no controls visible)
  - Verify board/questions display correctly
  - Verify score footer shows player scores

#### Suite 3: Multi-Client Synchronization (High Value!)
- [ ] `app/tests/e2e/multi-client-sync.spec.ts`:
  - **Host selects board → Presenter sees it**
    - Host context: select board A
    - Presenter context: verify board A is active
  - **Host reveals category → Presenter sees it**
    - Host: reveal category "History"
    - Presenter: verify "History" questions visible
  - **Host selects question → Presenter sees full-screen**
    - Host: click question
    - Presenter: verify question text in full-screen
  - **Host marks answered → Presenter sees visual update**
    - Host: toggle answered state
    - Presenter: verify question greyed out
  - **Host updates score → Presenter sees new score**
    - Host: award 500 points to Team A
    - Presenter: verify Team A score increased by 500

#### Suite 4: WebSocket Reconnection (High Value!)
- [ ] `app/tests/e2e/websocket-reconnect.spec.ts`:
  - **Presenter reconnects and catches up**
    - Start host + presenter
    - Disconnect presenter (close WebSocket or tab)
    - Host makes changes (select question, update score)
    - Reconnect presenter
    - Verify presenter receives catch-up state
  - **Connection recovery with exponential backoff**
    - Monitor network tab for reconnection attempts
    - Verify exponential backoff pattern (100ms → 1000ms)

#### Suite 5: Buzzer System (High Value!)
- [ ] `app/tests/e2e/buzzer.spec.ts`:
  - **Enable buzzers → All clients see active state**
    - Host: enable buzzers
    - Presenter: verify buzzer indicator active
  - **Buzzer press → Lock and display winner**
    - Simulate WebSocket buzzer_pressed message
    - Verify first buzzer locks out others
    - Verify winner highlighted in UI
  - **Disable buzzers → Clear state**
    - Host: disable buzzers
    - Verify all clients clear buzzer state

#### Suite 6: Race Condition Handling (High Value!)
- [ ] `app/tests/e2e/race-conditions.spec.ts`:
  - **Out-of-order WebSocket messages rejected**
    - Send WebSocket message with version 42
    - Send WebSocket message with version 41 (older)
    - Verify version 41 is ignored (state doesn't regress)
  - **Concurrent score updates**
    - Two host clients update score simultaneously
    - Verify final score is consistent across all clients

#### Suite 7: Media Questions
- [ ] `app/tests/e2e/media-questions.spec.ts`:
  - Test question with image (verify img tag loaded)
  - Test question with video (verify video element present)
  - Test question with audio (verify audio element present)
  - Test "special" question (verify animation/sound in presentation mode)

### Phase 4: Error Handling & Edge Cases
- [ ] `app/tests/e2e/error-handling.spec.ts`:
  - **API errors**
    - Mock API failure (500 error)
    - Verify graceful error display
  - **WebSocket disconnect**
    - Force WebSocket close
    - Verify reconnection UI/behavior
  - **Invalid game ID**
    - Navigate to non-existent game
    - Verify 404 or error page

### Phase 5: CI/CD Integration
- [ ] Update `.github/workflows/frontend-ci.yml` to add parallel `e2e` job:
  - Create new job `e2e:` that runs in parallel with existing `test:` job
  - Same pattern as backend (separate jobs for test/lint, both run concurrently)
  - Install Playwright browsers: `bunx playwright install --with-deps chromium`
  - Set up Python and Django backend dependencies
  - Install backend requirements: `pip install -r service/requirements.lock`
  - Run Django migrations to create test database
  - Start backend server in background: `cd service && python manage.py runserver 8000 &`
  - Wait for backend health check
  - Load test game via import API using `service/fixtures/test_game.json`
  - Run E2E tests: `cd app && bun run test:e2e`
  - Upload test artifacts on failure (screenshots, videos, HTML report)
  - Ensure tests run in headless mode
- [ ] Configure reasonable timeouts for CI (tests may be slower than local)

### Phase 6: Documentation & Developer Experience
- [ ] Update `TESTING.md`:
  - Add section on E2E testing with Playwright
  - Document how to run tests locally
  - Explain multi-client testing patterns
  - Note test database setup
- [ ] Update `CLAUDE.md`:
  - Add E2E test command to quality checks
  - Update "Quick Reference" section
- [ ] Create `app/tests/e2e/README.md`:
  - Explain test architecture
  - How to write new E2E tests
  - How to debug failing tests
  - Multi-client fixture usage examples

## Test Files Structure

```
app/
├── playwright.config.ts          # Chromium only, headless for CI
├── tests/
│   └── e2e/
│       ├── setup/
│       │   ├── backend-manager.ts
│       │   ├── database-manager.ts
│       │   ├── fixtures.ts
│       │   ├── global-setup.ts
│       │   └── global-teardown.ts
│       ├── host-basic.spec.ts
│       ├── presenter-basic.spec.ts
│       ├── multi-client-sync.spec.ts
│       ├── websocket-reconnect.spec.ts
│       ├── buzzer.spec.ts
│       ├── race-conditions.spec.ts
│       ├── media-questions.spec.ts
│       ├── error-handling.spec.ts
│       └── README.md
└── package.json (updated scripts)

service/
└── fixtures/
    └── test_game.json            # Test game data for import API
```

## CI/CD Parallel Execution

Frontend CI will run 3 jobs in parallel (like backend's test/lint pattern):

```yaml
jobs:
  test:           # Existing - lint, type-check, unit tests, build
  e2e:            # NEW - E2E tests with real backend
```

This ensures E2E tests don't slow down the main test job, and failures are isolated.

## Example Test Structure

```typescript
// app/tests/e2e/multi-client-sync.spec.ts
import { test, expect } from '@playwright/test';
import { multiClientFixture } from './setup/fixtures';

test.describe('Multi-Client Synchronization', () => {
  test('host selects question, presenter sees full-screen', async ({ browser }) => {
    const hostContext = await browser.newContext();
    const presenterContext = await browser.newContext();

    const hostPage = await hostContext.newPage();
    const presenterPage = await presenterContext.newPage();

    // Navigate to same game, different modes
    await hostPage.goto('/test-game-123/host');
    await presenterPage.goto('/test-game-123/presentation');

    // Host clicks question
    await hostPage.click('[data-testid="question-1-1"]');

    // Presenter sees full-screen question (wait for WebSocket update)
    await expect(presenterPage.locator('[data-testid="question-fullscreen"]'))
      .toBeVisible({ timeout: 2000 });
    await expect(presenterPage.locator('[data-testid="question-text"]'))
      .toContainText('What is the capital of France?');
  });
});
```

## Testing Philosophy Alignment

Following principles from `TESTING.md`:

✅ **High-Value Tests:**
- Multi-client synchronization (complex, critical)
- WebSocket reconnection (edge case, hard to test manually)
- Race condition handling (prevents bugs)
- Buzzer competition (business logic)

❌ **Avoid Low-Value Tests:**
- Testing every button click in isolation
- Testing CSS/styling (use visual regression if needed)
- Testing framework behavior (Svelte rendering)
- Redundant coverage of unit-tested logic

## Performance Targets

- Full E2E suite: **< 2 minutes** (with parallel workers)
- Single test file: **< 30 seconds**
- CI pipeline E2E step: **< 3 minutes** (including setup)

## Dependencies

**New:**
- `@playwright/test` - E2E testing framework
- Playwright browsers (chromium, firefox, webkit)

**Existing:**
- Django dev server (already available)
- SQLite (already used for dev/test)
- WebSocket support (already implemented)

## Security Considerations

- Test database should NOT contain real user data
- Use dummy/fake data for teams, players, questions
- Ensure test server is not exposed to network (localhost only)
- Add `.env.test` for test-specific config if needed

## Priority

**Medium-High** - Provides significant value for catching integration bugs, especially for WebSocket synchronization. Should be implemented after basic frontend features are stable.

## Related TODOs

- TODO #19: Game Import/Export (provides Option B for test data loading)
- Existing unit tests in `app/src/lib/*.test.ts` (complementary, not replaced)

## Success Criteria

- [ ] E2E tests run in CI/CD pipeline
- [ ] Multi-client synchronization verified end-to-end
- [ ] WebSocket reconnection tested automatically
- [ ] Tests catch at least one real integration bug before production
- [ ] Developer documentation makes it easy to add new E2E tests
- [ ] Test suite runs in < 2 minutes locally, < 3 minutes in CI
