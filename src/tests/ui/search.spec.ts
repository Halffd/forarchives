import { test, expect } from '@playwright/test';

test.describe('Search functionality', () => {
  test('should perform basic search', async ({ page }) => {
    await page.goto('/');
    
    // Fill search form
    await page.fill('ion-input[formControlName="query"]', 'test query');
    await page.check('ion-checkbox >> nth=0'); // Select first archive
    
    // Submit search
    await page.click('ion-button[type="submit"]');
    
    // Wait for results
    await expect(page.locator('.results-container')).toBeVisible();
    
    // Verify results structure
    await expect(page.locator('ion-card.result-card')).toHaveCount.above(0);
  });

  test('should show error when no archive selected', async ({ page }) => {
    await page.goto('/');
    
    await page.fill('ion-input[formControlName="query"]', 'test');
    await page.click('ion-button[type="submit"]');
    
    // Check for error message
    await expect(page.locator('text=Please select at least one archive')).toBeVisible();
  });

  test('should display search statistics', async ({ page }) => {
    await page.goto('/');
    
    await page.fill('ion-input[formControlName="query"]', 'test');
    await page.check('ion-checkbox >> nth=0');
    await page.click('ion-button[type="submit"]');
    
    // Verify statistics are shown
    await expect(page.locator('ion-badge')).toBeVisible();
  });
}); 