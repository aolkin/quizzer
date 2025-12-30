import { test, expect } from '@playwright/test';

test.describe('Presentation Mode - Basic Operations', () => {
  test.beforeEach(async ({ page }) => {
    const gameId = process.env.TEST_GAME_ID || '1';
    await page.goto(`/${gameId}/presentation`);
    await page.waitForLoadState('networkidle');
  });

  test('loads game page in presentation mode', async ({ page }) => {
    await expect(page.locator('[data-testid="score-footer"]')).toBeVisible({ timeout: 5000 });
  });

  test('does not show host controls', async ({ page }) => {
    await expect(page.locator('[data-testid="buzzer-toggle"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="present-question"]')).not.toBeVisible();
  });

  test('shows team information in footer', async ({ page }) => {
    await expect(page.locator('[data-testid^="team-"]').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid^="team-score-"]').first()).toBeVisible();
  });

  test('does not show point control buttons', async ({ page }) => {
    await expect(page.locator('[data-testid^="award-points-"]')).not.toBeVisible();
    await expect(page.locator('[data-testid^="deduct-points-"]')).not.toBeVisible();
  });
});
