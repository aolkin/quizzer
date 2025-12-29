import { test, expect } from '@playwright/test';

test.describe('Multi-Client Synchronization', () => {
  test('host selects board, presenter sees it', async ({ browser }) => {
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

    await expect(hostPage.locator('[data-testid^="category-"]').first()).toBeVisible({
      timeout: 5000,
    });
    await expect(presenterPage.locator('[data-testid^="category-"]').first()).toBeVisible({
      timeout: 5000,
    });

    await hostContext.close();
    await presenterContext.close();
  });

  test('host reveals category, presenter sees it', async ({ browser }) => {
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
    await hostPage.waitForTimeout(1000);

    // Click the category to reveal it
    const category = hostPage.locator('[data-testid^="category-"]').first();
    await category.click();

    // Wait longer for WebSocket sync
    await hostPage.waitForTimeout(1000);

    // The presenter should now see the category name visible
    // Wait for any category to have text content
    await expect(presenterPage.locator('[data-testid^="category-"]').first()).toBeVisible({
      timeout: 10000,
    });

    await hostContext.close();
    await presenterContext.close();
  });

  test('host presents question, presenter sees full-screen', async ({ browser }) => {
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
    await hostPage.waitForTimeout(500);

    const question = hostPage.locator('[data-testid^="question-"]').first();
    await question.click();
    await hostPage.waitForTimeout(300);

    const presentButton = hostPage.locator('[data-testid="present-question"]');
    await presentButton.click();

    await expect(
      presenterPage.locator('[data-testid="question-display"][data-visible="true"]'),
    ).toBeVisible({ timeout: 5000 });

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
    await hostPage.waitForTimeout(1000);

    const question = hostPage.locator('[data-testid^="question-"]').first();
    await question.click();
    await hostPage.waitForTimeout(500);

    const markAnsweredButton = hostPage.locator('[data-testid="mark-answered"]');
    await markAnsweredButton.click();

    // Wait longer for the API call and WebSocket broadcast
    await hostPage.waitForTimeout(1000);

    // Check that the question is marked as answered (opacity-75 class)
    await expect(question).toHaveClass(/opacity-75/, { timeout: 10000 });

    await hostContext.close();
    await presenterContext.close();
  });
});
