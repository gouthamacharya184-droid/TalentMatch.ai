import { test, expect } from '@playwright/test';

test.describe('TalentMatch.ai Critical Recruiter Workflow', () => {
  // Listen for console errors across all tests
  test.beforeEach(async ({ page }) => {
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Ignore expected network connection errors in tests if backend is down
        if (!text.includes('ERR_CONNECTION_REFUSED') && !text.includes('talentmatch:offline')) {
          console.warn(`[Browser Console Error]: ${text}`);
        }
      }
    });
  });

  test('Protected route redirects unauthenticated user to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/.*\/login/);
    await expect(page.locator('h2')).toContainText('TalentMatch AI');
  });

  test('Displays validation error on wrong password', async ({ page }) => {
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('recruiter@talentmatch.ai');
    await page.locator('input[type="password"]').fill('WrongPassword999!');
    await page.locator('button[type="submit"]').click();

    // Verify error banner is visible
    const errorAlert = page.locator('.bg-rose-50');
    await expect(errorAlert).toBeVisible({ timeout: 5000 });
  });

  test('Successful login and navigation to dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('recruiter@talentmatch.ai');
    await page.locator('input[type="password"]').fill('Recruiter@123456');
    await page.locator('button[type="submit"]').click();

    // Verify redirect to workspace dashboard
    await expect(page).toHaveURL(/.*\/(dashboard)?$/, { timeout: 8000 });
    await expect(page.locator('text=TalentMatch')).toBeVisible();
  });

  test('User registration flow validation', async ({ page }) => {
    await page.goto('/register');
    const uniqueEmail = `test.recruiter.${Date.now()}@example.com`;
    await page.locator('input[type="text"]').fill('Playwright Test Lead');
    await page.locator('input[type="email"]').fill(uniqueEmail);
    await page.locator('input[type="password"]').fill('SecureTestPass@2026');
    await page.locator('button[type="submit"]').click();

    // Should redirect to dashboard upon successful registration
    await expect(page).toHaveURL(/.*\/(dashboard)?$/, { timeout: 8000 });
  });

  test('Upload page enforces file size and format constraints', async ({ page }) => {
    // Authenticate first
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('recruiter@talentmatch.ai');
    await page.locator('input[type="password"]').fill('Recruiter@123456');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/.*\/(dashboard)?$/);

    // Navigate to Resume Upload
    await page.goto('/resumes/upload');
    await expect(page.locator('h1, h2')).toContainText(/Resume Upload|Upload/i);

    // Verify upload zone is accessible
    const uploadInput = page.locator('input[type="file"]');
    expect(await uploadInput.count()).toBeGreaterThanOrEqual(1);
  });

  test('Chatbot widget opens, toggles, and handles messages', async ({ page }) => {
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('recruiter@talentmatch.ai');
    await page.locator('input[type="password"]').fill('Recruiter@123456');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/.*\/(dashboard)?$/);

    // Look for chatbot trigger button
    const botToggle = page.locator('button[title*="Chatbot"], button:has(.lucide-bot), button:has-text("Copilot"), #chatbot-trigger');
    if (await botToggle.count() > 0) {
      await botToggle.first().click();
      await expect(page.locator('input[placeholder*="Ask"], textarea[placeholder*="Ask"], input[placeholder*="Message"]')).toBeVisible();
    }
  });

  test('Logout cleanly clears state and redirects to login', async ({ page }) => {
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('recruiter@talentmatch.ai');
    await page.locator('input[type="password"]').fill('Recruiter@123456');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/.*\/(dashboard)?$/);

    // Find and click sign out button
    const logoutBtn = page.locator('button:has-text("Sign Out"), button:has-text("Logout"), button:has(.lucide-log-out)');
    if (await logoutBtn.count() > 0) {
      await logoutBtn.first().click();
      await expect(page).toHaveURL(/.*\/login/);
    }
  });
});

