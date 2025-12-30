import { defineConfig, devices } from '@playwright/test';

// Use webServer in CI to automatically start servers
// Locally, start servers manually for faster iteration
const useWebServer = !!process.env.CI;

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : 4,
  reporter: [['html', { open: 'never' }], ['list']],

  globalSetup: './tests/e2e/setup/global-setup.ts',
  globalTeardown: './tests/e2e/setup/global-teardown.ts',

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  timeout: 30 * 1000,
  expect: {
    timeout: 5 * 1000,
  },

  // Automatically start backend and frontend servers in CI
  ...(useWebServer && {
    webServer: [
      {
        command: 'cd ../service && python manage.py runserver 8000',
        url: 'http://localhost:8000/api/game/1/',
        reuseExistingServer: !process.env.CI,
        timeout: 30 * 1000,
      },
      {
        command: 'VITE_API_ENDPOINT=localhost:8000 bun run dev',
        url: 'http://localhost:5173',
        reuseExistingServer: !process.env.CI,
        timeout: 30 * 1000,
      },
    ],
  }),
});
