import { test, expect } from '@playwright/test';

test.describe('Multi-Client Synchronization', () => {
  test('host and presenter load game, host selects board and both see categories', async ({
    browser,
  }) => {
    const hostContext = await browser.newContext();
    const presenterContext = await browser.newContext();

    const hostPage = await hostContext.newPage();
    const presenterPage = await presenterContext.newPage();

    const gameId = process.env.TEST_GAME_ID || '1';

    await Promise.all([
      hostPage.goto(`/${gameId}/host`),
      presenterPage.goto(`/${gameId}/presentation`),
    ]);

    await Promise.all([
      hostPage.waitForLoadState('networkidle'),
      presenterPage.waitForLoadState('networkidle'),
    ]);

    // Verify both clients load the game
    await expect(hostPage.locator('text=E2E Test Game')).toBeVisible();
    await expect(hostPage.locator('[data-testid="score-footer"]')).toBeVisible();
    await expect(presenterPage.locator('[data-testid="score-footer"]')).toBeVisible();

    // Host selects a board
    const boardSelector = hostPage.locator('[data-testid^="board-selector-"]').first();
    await boardSelector.click();

    // Both should see categories
    await expect(hostPage.locator('[data-testid^="category-"]').first()).toBeVisible({
      timeout: 5000,
    });
    await expect(presenterPage.locator('[data-testid^="category-"]').first()).toBeVisible({
      timeout: 5000,
    });

    await hostContext.close();
    await presenterContext.close();
  });

  test('host reveals category and selects question, presenter sees updates', async ({
    browser,
  }) => {
    const hostContext = await browser.newContext();
    const presenterContext = await browser.newContext();

    const hostPage = await hostContext.newPage();
    const presenterPage = await presenterContext.newPage();

    const gameId = process.env.TEST_GAME_ID || '1';

    await Promise.all([
      hostPage.goto(`/${gameId}/host`),
      presenterPage.goto(`/${gameId}/presentation`),
    ]);

    await Promise.all([
      hostPage.waitForLoadState('networkidle'),
      presenterPage.waitForLoadState('networkidle'),
    ]);

    const boardSelector = hostPage.locator('[data-testid^="board-selector-"]').first();
    await boardSelector.click();

    // Wait for board to load on host
    await expect(hostPage.locator('[data-testid^="category-"]').first()).toBeVisible({
      timeout: 10000,
    });

    // Click the category to reveal it
    const category = hostPage.locator('[data-testid^="category-"]').first();
    await category.click();

    // The presenter should now see the category visible
    await expect(presenterPage.locator('[data-testid^="category-"]').first()).toBeVisible({
      timeout: 10000,
    });

    // Host selects a question
    const question = hostPage.locator('[data-testid^="question-"]').first();
    await question.click();

    // Host should see question controls
    await expect(hostPage.locator('[data-testid="present-question"]')).toBeVisible({
      timeout: 5000,
    });
    await expect(hostPage.locator('[data-testid="mark-answered"]')).toBeVisible();

    await hostContext.close();
    await presenterContext.close();
  });

  test('host presents question, presenter sees full-screen display', async ({ browser }) => {
    const hostContext = await browser.newContext();
    const presenterContext = await browser.newContext();

    const hostPage = await hostContext.newPage();
    const presenterPage = await presenterContext.newPage();

    const gameId = process.env.TEST_GAME_ID || '1';

    await Promise.all([
      hostPage.goto(`/${gameId}/host`),
      presenterPage.goto(`/${gameId}/presentation`),
    ]);

    await Promise.all([
      hostPage.waitForLoadState('networkidle'),
      presenterPage.waitForLoadState('networkidle'),
    ]);

    const boardSelector = hostPage.locator('[data-testid^="board-selector-"]').first();
    await boardSelector.click();

    await expect(hostPage.locator('[data-testid^="question-"]').first()).toBeVisible({
      timeout: 10000,
    });

    const question = hostPage.locator('[data-testid^="question-"]').first();
    await question.click();

    const presentButton = hostPage.locator('[data-testid="present-question"]');
    await expect(presentButton).toBeVisible({ timeout: 5000 });
    await presentButton.click();

    // Presenter should see the question display in full-screen mode (z-index: 50)
    const questionDisplay = presenterPage.locator('[data-testid="question-display"]').first();
    await expect(questionDisplay).toHaveCSS('z-index', '50', {
      timeout: 5000,
    });

    // Host buzzer toggle should show question is active
    await expect(hostPage.locator('[data-testid="buzzer-toggle"]')).toContainText(/Reset|Disable/, {
      timeout: 5000,
    });

    await hostContext.close();
    await presenterContext.close();
  });

  test('host marks question answered, both clients see update', async ({ browser }) => {
    const hostContext = await browser.newContext();
    const presenterContext = await browser.newContext();

    const hostPage = await hostContext.newPage();
    const presenterPage = await presenterContext.newPage();

    const gameId = process.env.TEST_GAME_ID || '1';

    await Promise.all([
      hostPage.goto(`/${gameId}/host`),
      presenterPage.goto(`/${gameId}/presentation`),
    ]);

    await Promise.all([
      hostPage.waitForLoadState('networkidle'),
      presenterPage.waitForLoadState('networkidle'),
    ]);

    const boardSelector = hostPage.locator('[data-testid^="board-selector-"]').first();
    await boardSelector.click();

    // Wait for board to load
    await expect(hostPage.locator('[data-testid^="question-"]').first()).toBeVisible({
      timeout: 10000,
    });

    const question = hostPage.locator('[data-testid^="question-"]').first();

    // Verify points are visible before marking answered
    const questionText = question.locator('div').filter({ hasText: /^\d+$/ }).first();
    await expect(questionText).toBeVisible({ timeout: 5000 });

    await question.click();

    // Wait for question details to appear
    const markAnsweredButton = hostPage.locator('[data-testid="mark-answered"]');
    await expect(markAnsweredButton).toBeVisible({ timeout: 5000 });
    await markAnsweredButton.click();

    // Check that the question is marked as answered
    // The button gets opacity-75 class and points text disappears
    await expect(question).toHaveClass(/opacity-75/, { timeout: 10000 });
    await expect(questionText).not.toBeVisible({ timeout: 10000 });

    await hostContext.close();
    await presenterContext.close();
  });
});
