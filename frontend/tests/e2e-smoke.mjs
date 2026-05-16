import { spawn } from "node:child_process";
import process from "node:process";
import { chromium } from "@playwright/test";

const vite = spawn(
  process.execPath,
  ["./node_modules/vite/bin/vite.js", "--host", "127.0.0.1", "--port", "3000", "--strictPort"],
  { stdio: "inherit" },
);

async function waitForServer(url, retries = 40) {
  for (let attempt = 0; attempt < retries; attempt += 1) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
    } catch {
      // Keep waiting while Vite starts.
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error("Timed out waiting for frontend dev server.");
}

async function stopVite() {
  if (vite.killed) {
    return;
  }

  if (process.platform === "win32") {
    await new Promise((resolve) => {
      const killer = spawn("taskkill", ["/pid", String(vite.pid), "/T", "/F"]);
      killer.on("exit", resolve);
    });
    return;
  }

  vite.kill("SIGTERM");
}

async function run() {
  let browser;
  try {
    await waitForServer("http://127.0.0.1:3000");
    browser = await chromium.launch();
    const page = await browser.newPage();
    await page.addInitScript(() => {
      localStorage.setItem("access_token", "token-1");
    });

    await page.route("**/api/health", async (route) => {
      await route.fulfill({ json: { status: "ok" } });
    });

    await page.route("**/api/chat", async (route) => {
      await route.fulfill({
        json: {
          answer: "Grounded answer [1]",
          citations: [
            {
              document_id: "doc-1",
              title: "sample.pdf",
              page_number: 4,
              chunk_id: "chunk-1",
              excerpt: "Relevant source excerpt",
              score: 0.91,
            },
          ],
        },
      });
    });

    await page.route("**/api/documents", async (route) => {
      await route.fulfill({ json: [] });
    });

    await page.route("**/api/auth/me", async (route) => {
      await route.fulfill({
        json: { user_id: "user-1", email: "user@example.com", role: "user" },
      });
    });

    await page.goto("http://127.0.0.1:3000");
    await page.getByText("Japanese Enterprise Knowledge Assistant").waitFor();
    await page.locator("textarea").fill("What is this document about?");
    await page.getByRole("button", { name: "Ask" }).click();
    await page.getByText("Grounded answer [1]").waitFor();
    await page.getByText("sample.pdf").waitFor();
    await page.getByText("Page 4").waitFor();
    console.log("E2E smoke test passed.");
  } finally {
    if (browser) {
      await browser.close();
    }
    await stopVite();
  }
}

run()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
