import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:3000",
  },
  webServer: {
    command: "node ./node_modules/vite/bin/vite.js --host 127.0.0.1 --port 3000 --strictPort",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: false,
    stdout: "pipe",
    stderr: "pipe",
  },
});
