import { test, expect } from '@playwright/test';

test.describe('Search API', () => {
  const API_URL = 'http://localhost:8888';

  test('should return search results', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/search`, {
      data: {
        query: 'test',
        archives: [0]
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.results).toBeDefined();
  });

  test('should handle invalid archive indices', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/search`, {
      data: {
        query: 'test',
        archives: [999]
      }
    });
    
    expect(response.ok()).toBeFalsy();
  });
}); 