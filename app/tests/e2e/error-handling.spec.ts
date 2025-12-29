import { test, expect } from '@playwright/test';

test.describe('Error Handling', () => {
  test('invalid game ID shows error or redirects', async ({ page }) => {
    await page.goto('/99999/host');
    await page.waitForLoadState('networkidle');

    const hasError =
      (await page.locator('text=/error|not found|404/i').count()) > 0 ||
      (await page.locator('[class*="error"]').count()) > 0;

    expect(hasError || page.url().includes('error') || page.url() === '/').toBeTruthy();
  });

  test('gracefully handles missing game data', async ({ page }) => {
    const gameId = process.env.TEST_GAME_ID || '1';
    await page.goto(`/${gameId}/host`);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('[data-testid="score-footer"]')).toBeVisible({ timeout: 5000 });
  });
});
