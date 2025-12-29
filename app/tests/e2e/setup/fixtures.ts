import { test as base, expect, type Page, type BrowserContext } from '@playwright/test';

export interface GameContext {
  gameId: number;
  hostPage: Page;
  presenterPage: Page;
  hostContext: BrowserContext;
  presenterContext: BrowserContext;
}

export const test = base.extend<{
  gameContext: GameContext;
}>({
  gameContext: async ({ browser }, use) => {
    const hostContext = await browser.newContext();
    const presenterContext = await browser.newContext();

    const hostPage = await hostContext.newPage();
    const presenterPage = await presenterContext.newPage();

    const gameId = parseInt(process.env.TEST_GAME_ID || '1');

    await use({
      gameId,
      hostPage,
      presenterPage,
      hostContext,
      presenterContext,
    });

    await hostPage.close();
    await presenterPage.close();
    await hostContext.close();
    await presenterContext.close();
  },
});

export { expect };

export async function waitForWebSocketConnection(page: Page, timeout = 5000): Promise<void> {
  await page.waitForFunction(
    () => {
      const ws = (window as unknown as { __gameWebSocket?: { readyState: number } })
        .__gameWebSocket;
      return ws && ws.readyState === WebSocket.OPEN;
    },
    { timeout },
  );
}

export async function selectBoard(hostPage: Page, boardId: number): Promise<void> {
  await hostPage.click(`[data-testid="board-selector-${boardId}"]`);
}

export async function selectQuestion(
  hostPage: Page,
  categoryIndex: number,
  questionIndex: number,
): Promise<void> {
  await hostPage.click(`[data-testid="question-${categoryIndex}-${questionIndex}"]`);
}

export async function waitForQuestionDisplay(page: Page): Promise<void> {
  await expect(page.locator('[data-testid="question-display"]')).toBeVisible();
}

export async function closeQuestion(hostPage: Page): Promise<void> {
  await hostPage.click('[data-testid="close-question"]');
}
