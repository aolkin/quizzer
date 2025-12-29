import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const API_BASE_URL = 'http://localhost:8000';

async function waitForBackend(maxRetries = 30, delayMs = 1000): Promise<void> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/game/1/`, {
        method: 'GET',
      });
      if (response.ok || response.status === 404) {
        console.log('Backend is ready');
        return;
      }
    } catch {
      // Server not ready yet
    }
    console.log(`Waiting for backend... (${i + 1}/${maxRetries})`);
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  throw new Error('Backend failed to start');
}

async function loadTestGame(): Promise<number> {
  const fixturePath = path.resolve(__dirname, '../../../../service/fixtures/test_game.json');

  if (!fs.existsSync(fixturePath)) {
    throw new Error(`Test fixture not found: ${fixturePath}`);
  }

  const fixtureData = JSON.parse(fs.readFileSync(fixturePath, 'utf-8'));

  const response = await fetch(`${API_BASE_URL}/api/game/import/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(fixtureData),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to import test game: ${error}`);
  }

  const result = (await response.json()) as { game_id: number };
  console.log(`Test game imported with ID: ${result.game_id}`);
  return result.game_id;
}

export default async function globalSetup(): Promise<void> {
  console.log('Global setup: Starting...');

  await waitForBackend();

  const gameId = await loadTestGame();

  process.env.TEST_GAME_ID = gameId.toString();

  console.log('Global setup: Complete');
}
