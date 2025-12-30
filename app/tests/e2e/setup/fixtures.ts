// Re-export Playwright's base test and expect.
// Custom game-specific fixtures were removed as they were not used in tests.
// Tests manually create browser contexts for multi-client scenarios.
export { test, expect } from '@playwright/test';
