import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./src/test",
  testMatch: /.*\.spec\.ts/,
  timeout: 45000,
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "Desktop Chrome",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "Mobile Chrome",
      use: { ...devices["Pixel 5"] },
    },
  ],
});
