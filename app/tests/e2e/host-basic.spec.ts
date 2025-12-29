import { test, expect } from '@playwright/test';

test.describe('Host Mode - Basic Operations', () => {
  test.beforeEach(async ({ page }) => {
    const gameId = process.env.TEST_GAME_ID || '1';
    await page.goto(`/${gameId}/host`);
    await page.waitForLoadState('networkidle');
  });

  test('loads game page in host mode', async ({ page }) => {
    await expect(page.locator('text=E2E Test Game')).toBeVisible();
    await expect(page.locator('[data-testid="score-footer"]')).toBeVisible();
  });

  test('can select a board', async ({ page }) => {
    const boardSelector = page.locator('[data-testid^="board-selector-"]').first();
    await boardSelector.click();
    await expect(page.locator('[data-testid^="category-"]').first()).toBeVisible({ timeout: 5000 });
  });

  test('can reveal categories', async ({ page }) => {
    const boardSelector = page.locator('[data-testid^="board-selector-"]').first();
    await boardSelector.click();
    await page.waitForTimeout(500);

    const category = page.locator('[data-testid^="category-"]').first();
    await category.click();

    await expect(category).toBeVisible();
  });

  test('can select and view question details', async ({ page }) => {
    const boardSelector = page.locator('[data-testid^="board-selector-"]').first();
    await boardSelector.click();
    await page.waitForTimeout(500);

    const question = page.locator('[data-testid^="question-"]').first();
    await question.click();

    await expect(page.locator('[data-testid="present-question"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="mark-answered"]')).toBeVisible();
  });

  test('can present question to viewers', async ({ page }) => {
    const boardSelector = page.locator('[data-testid^="board-selector-"]').first();
    await boardSelector.click();
    await page.waitForTimeout(500);

    const question = page.locator('[data-testid^="question-"]').first();
    await question.click();
    await page.waitForTimeout(300);

    const presentButton = page.locator('[data-testid="present-question"]');
    await expect(presentButton).toBeVisible({ timeout: 5000 });
    await presentButton.click();

    // In host mode, clicking Present sends a WebSocket message
    // The full-screen display appears on presentation clients, not host
    // Verify the buzzer toggle appeared (indicating question is now "active")
    await expect(page.locator('[data-testid="buzzer-toggle"]')).toContainText(/Reset|Disable/, {
      timeout: 5000,
    });
  });

  test('shows player scores in footer', async ({ page }) => {
    await expect(page.locator('[data-testid^="player-score-"]').first()).toBeVisible({
      timeout: 5000,
    });
  });

  test('buzzer toggle button is visible', async ({ page }) => {
    await expect(page.locator('[data-testid="buzzer-toggle"]')).toBeVisible({ timeout: 5000 });
  });
});
