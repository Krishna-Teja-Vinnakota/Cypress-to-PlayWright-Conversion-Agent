import { test, expect } from '@playwright/test';

test.describe('Profile Form Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test('Test 1: Should show error when name is less than 3 characters', async ({ page }) => {
    await page.locator('[data-testid="name-input"]').fill('Jo');
    await page.locator('[data-testid="name-input"]').blur();
    await expect(page.locator('[data-testid="name-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="name-error"]')).toContainText('Name must be at least 3 characters');
  });

  test('Test 2: Should accept valid name with 3+ characters', async ({ page }) => {
    await page.locator('[data-testid="name-input"]').fill('John Doe');
    await page.locator('[data-testid="name-input"]').blur();
    await expect(page.locator('[data-testid="name-error"]')).toHaveCount(0);
  });

  test('Test 3: Should show error for invalid email format', async ({ page }) => {
    await page.locator('[data-testid="email-input"]').fill('invalidemail.com');
    await page.locator('[data-testid="email-input"]').blur();
    await expect(page.locator('[data-testid="email-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-error"]')).toContainText('Please enter a valid email address');
  });

  test('Test 4: Should show error when phone number is not exactly 10 digits', async ({ page }) => {
    await page.locator('[data-testid="phone-input"]').fill('12345');
    await page.locator('[data-testid="phone-input"]').blur();
    await expect(page.locator('[data-testid="phone-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="phone-error"]')).toContainText('Phone number must be exactly 10 digits');
  });

  test('Test 5: Should show error when age is less than 18', async ({ page }) => {
    await page.locator('[data-testid="age-input"]').fill('17');
    await page.locator('[data-testid="age-input"]').blur();
    await expect(page.locator('[data-testid="age-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="age-error"]')).toContainText('Age must be at least 18');
  });

  test('Test 6: Should show error when bio exceeds 200 characters', async ({ page }) => {
    const longBio = 'a'.repeat(201);
    await page.locator('[data-testid="bio-input"]').fill(longBio);
    await page.locator('[data-testid="bio-input"]').blur();
    await expect(page.locator('[data-testid="bio-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="bio-error"]')).toContainText('Bio must not exceed 200 characters');
  });

  test('Test 7: Should disable submit button when form is invalid', async ({ page }) => {
    await page.locator('[data-testid="name-input"]').fill('Jo'); // Invalid - too short
    await page.locator('[data-testid="email-input"]').fill('test@test.com');
    await page.locator('[data-testid="phone-input"]').fill('1234567890');
    await page.locator('[data-testid="age-input"]').fill('25');
    await expect(page.locator('[data-testid="save-button"]')).toBeDisabled();
  });

  test('Test 8: Should enable submit button and submit successfully with all valid data', async ({ page }) => {
    // Fill all fields with valid data
    await page.locator('[data-testid="name-input"]').fill('John Doe');
    await page.locator('[data-testid="email-input"]').fill('john.doe@example.com');
    await page.locator('[data-testid="phone-input"]').fill('1234567890');
    await page.locator('[data-testid="age-input"]').fill('30');
    await page.locator('[data-testid="bio-input"]').fill('Software Engineer');

    // Verify button is enabled
    await expect(page.locator('[data-testid="save-button"]')).toBeEnabled();

    // Mock the API call
    await page.route('http://localhost:3001/api/profile', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ message: 'Profile updated successfully' }),
      });
    });

    // Submit the form
    await page.locator('[data-testid="save-button"]').click();

    // Verify submission
    await page.waitForResponse(response => response.url().includes('/api/profile') && response.status() === 200);
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Profile updated successfully');
  });

  test('Test 9: Should accept valid email with various formats', async ({ page }) => {
    await page.locator('[data-testid="email-input"]').fill('user.name+tag@example.co.uk');
    await page.locator('[data-testid="email-input"]').blur();
    await expect(page.locator('[data-testid="email-error"]')).toHaveCount(0);
  });

  test('Test 10: Should accept exactly 200 characters in bio (boundary test)', async ({ page }) => {
    const exactBio = 'a'.repeat(200);
    await page.locator('[data-testid="bio-input"]').fill(exactBio);
    await page.locator('[data-testid="bio-input"]').blur();
    await expect(page.locator('[data-testid="bio-error"]')).toHaveCount(0);
  });
});