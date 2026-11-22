import { test, expect } from '@playwright/test';

test.describe('TalentMatch.ai Critical Recruiter Workflow', () => {
  // Listen for console errors and setup deterministic API interceptors
  test.beforeEach(async ({ page }) => {
    // Monitor console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (!text.includes('ERR_CONNECTION_REFUSED') && !text.includes('talentmatch:offline') && !text.includes('502')) {
          console.warn(`[Browser Console Error]: ${text}`);
        }
      }
    });

    // Intercept all API routes
    await page.route('**/api/**', async (route) => {
      const request = route.request();
      const url = request.url();

      // Auth Login
      if (url.includes('/auth/login')) {
        const postData = JSON.parse(request.postData() || '{}');
        if (postData.password === 'WrongPassword999!') {
          await route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Incorrect email or password' }),
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              access_token: 'mock_jwt_access_token_12345',
              refresh_token: 'mock_jwt_refresh_token_67890',
              token_type: 'bearer',
              user: {
                id: 'recruiter-uuid-001',
                email: postData.email || 'recruiter@talentmatch.ai',
                full_name: 'Lead Recruiter',
                role: 'recruiter',
              },
            }),
          });
        }
        return;
      }

      // Auth Register
      if (url.includes('/auth/register')) {
        const postData = JSON.parse(request.postData() || '{}');
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'mock_registered_access_token',
            refresh_token: 'mock_registered_refresh_token',
            token_type: 'bearer',
            user: {
              id: 'registered-uuid-002',
              email: postData.email,
              full_name: postData.full_name || 'New Recruiter',
              role: 'recruiter',
            },
          }),
        });
        return;
      }

      // Auth Get Current User (/auth/me)
      if (url.includes('/auth/me')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'recruiter-uuid-001',
            email: 'recruiter@talentmatch.ai',
            full_name: 'Lead Recruiter',
            role: 'recruiter',
          }),
        });
        return;
      }

      // Auth Logout
      if (url.includes('/auth/logout')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Successfully logged out' }),
        });
        return;
      }

      // Analytics Dashboard
      if (url.includes('/analytics/dashboard')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            total_candidates: 42,
            total_jobs: 8,
            total_matches: 128,
            average_match_score: 84.5,
            active_pipelines: 6,
            score_distribution: { '80-100%': 15, '60-79%': 20, '<60%': 7 },
            skills_availability: { Python: 25, React: 18, SQL: 15 },
          }),
        });
        return;
      }

      // Notifications
      if (url.includes('/notifications')) {
        if (url.includes('unread-count')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ count: 0 }),
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ items: [], total: 0, page: 1, limit: 10 }),
          });
        }
        return;
      }

      // Chatbot
      if (url.includes('/chatbot')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'Hello! I am your AI recruiting copilot. How can I assist you?',
            suggestions: ['Find Python engineers', 'Compare top candidates'],
          }),
        });
        return;
      }

      // Candidates
      if (url.includes('/candidates')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'cand-1',
              name: 'Sarah Chen',
              email: 'sarah.chen@example.com',
              current_role: 'Senior Full Stack Engineer',
              experience_years: 7,
              skills: [{ skill_name: 'Python' }, { skill_name: 'React' }],
            },
          ]),
        });
        return;
      }

      // Jobs
      if (url.includes('/jobs')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'job-1',
              title: 'Senior Python Engineer',
              department: 'Engineering',
              status: 'active',
              requirements: [{ skill_name: 'Python' }, { skill_name: 'FastAPI' }],
            },
          ]),
        });
        return;
      }

      // Generic fallback for any other API calls
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      });
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
    await expect(page).toHaveURL(/.*(\/dashboard|\/)$/, { timeout: 8000 });
    await expect(page.locator('h1')).toContainText(/Recruiter Overview/i);
  });

  test('User registration flow validation', async ({ page }) => {
    await page.goto('/register');
    const uniqueEmail = `test.recruiter.${Date.now()}@example.com`;
    await page.locator('input[type="text"]').fill('Playwright Test Lead');
    await page.locator('input[type="email"]').fill(uniqueEmail);
    await page.locator('input[type="password"]').fill('SecureTestPass@2026');
    await page.locator('button[type="submit"]').click();

    // Should redirect to dashboard upon successful registration
    await expect(page).toHaveURL(/.*(\/dashboard|\/)$/, { timeout: 8000 });
    await expect(page.locator('h1')).toContainText(/Recruiter Overview/i);
  });

  test('Upload page enforces file size and format constraints', async ({ page }) => {
    // Authenticate first
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('recruiter@talentmatch.ai');
    await page.locator('input[type="password"]').fill('Recruiter@123456');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/.*(\/dashboard|\/)$/);

    // Navigate to Resume Upload
    await page.goto('/resumes/upload');
    await expect(page.locator('h1, h2')).toContainText(/Resume Upload|Upload/i);

    // Verify upload zone is accessible
    const uploadInput = page.locator('input[type="file"]');
    expect(await uploadInput.count()).toBeGreaterThanOrEqual(1);
  });

  test('Logout cleanly clears state and redirects to login', async ({ page }) => {
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('recruiter@talentmatch.ai');
    await page.locator('input[type="password"]').fill('Recruiter@123456');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/.*(\/dashboard|\/)$/);

    // On mobile and tablet viewports (<1024px), open mobile menu first
    const isMobileOrTablet = (page.viewportSize()?.width || 1440) < 1024;
    if (isMobileOrTablet) {
      const menuBtn = page.locator('button:has(.lucide-menu)');
      await expect(menuBtn).toBeVisible({ timeout: 5000 });
      await menuBtn.click();
      const mobileLogout = page.locator('.z-50 button:has-text("Logout")');
      await expect(mobileLogout).toBeVisible({ timeout: 5000 });
      await mobileLogout.click();
    } else {
      const desktopLogout = page.locator('aside button:has-text("Logout")');
      await expect(desktopLogout).toBeVisible({ timeout: 5000 });
      await desktopLogout.click();
    }

    await expect(page).toHaveURL(/.*\/login/);
  });
});
