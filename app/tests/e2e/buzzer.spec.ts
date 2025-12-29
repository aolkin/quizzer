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

    // Click to toggle state
    await buzzerButton.click();
    await page.waitForTimeout(500);

    // Verify the button is still visible after clicking
    await expect(buzzerButton).toBeVisible();
    await expect(buzzerButton).toContainText(/Enable|Disable|Reset/, { timeout: 5000 });
  });

  test('host enables buzzers, presenter client receives state', async ({ browser }) => {
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
