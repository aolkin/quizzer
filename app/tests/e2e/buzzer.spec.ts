import { test, expect } from '@playwright/test';

test.describe('Buzzer System', () => {
  test('buzzer toggle button works', async ({ page }) => {
    const gameId = process.env.TEST_GAME_ID || '1';
    await page.goto(`/${gameId}/host`);
    await page.waitForLoadState('networkidle');

    const buzzerButton = page.locator('[data-testid="buzzer-toggle"]');
    await expect(buzzerButton).toBeVisible({ timeout: 5000 });

    // Check that buzzer button has one of the expected states
    await expect(buzzerButton).toContainText(/Enable|Disable|Reset/, { timeout: 5000 });

    // Click to toggle state - button should remain functional
    await buzzerButton.click();

    // Verify the button is still visible and in a valid state after clicking
    await expect(buzzerButton).toBeVisible({ timeout: 5000 });
    await expect(buzzerButton).toContainText(/Enable|Disable|Reset/, { timeout: 5000 });
  });

  test('host presents question, presenter shows full-screen question display', async ({
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

    // Select a board and wait for categories to appear
    const boardSelector = hostPage.locator('[data-testid^="board-selector-"]').first();
    await boardSelector.click();
    await expect(hostPage.locator('[data-testid^="category-"]').first()).toBeVisible({
      timeout: 5000,
    });

    // Select a question and wait for present button to appear
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

    await hostContext.close();
    await presenterContext.close();
  });
});
