import { expect, test } from "@playwright/test";

test("user can ask a question and see citations", async ({ page }) => {
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

  await page.goto("/");
  await expect(page.getByText("Japanese Enterprise Knowledge Assistant")).toBeVisible();
  await page.getByPlaceholder(/質問|è³ª/).fill("What is this document about?");
  await page.getByRole("button", { name: "Ask" }).click();

  await expect(page.getByText("Grounded answer [1]")).toBeVisible();
  await expect(page.getByText("sample.pdf")).toBeVisible();
  await expect(page.getByText("Page 4")).toBeVisible();
});

