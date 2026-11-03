import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e', globalSetup: './e2e/global-setup.ts', fullyParallel: false, workers: 1, timeout: 120000,
  reporter: [['list']], use: { baseURL: 'http://localhost:3003', actionTimeout: 10000, browserName: 'chromium', headless: true, launchOptions: { executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', args: ['--no-sandbox'] }, screenshot: 'only-on-failure', trace: 'retain-on-failure' },
});
