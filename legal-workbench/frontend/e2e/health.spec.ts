import { test, expect } from '@playwright/test'

/**
 * API Health Check Smoke Tests
 *
 * These tests verify that backend services are reachable and responding.
 * Note: These tests require the full Docker Compose stack to be running.
 * In CI, these should be run against a deployed environment.
 */
test.describe('API Health Checks', () => {
  // Skip these tests if not running against full stack
  // The preview server (vite preview) only serves static files
  const isFullStack = !!process.env.FULL_STACK || !!process.env.CI

  test.describe('Backend Service Health Endpoints', () => {
    const healthEndpoints = [
      { name: 'STJ API', endpoint: '/api/stj/health' },
      { name: 'Trello API', endpoint: '/api/trello/health' },
      { name: 'Text Extractor API', endpoint: '/api/text/health' },
      { name: 'Doc Assembler API', endpoint: '/api/doc/health' },
    ]

    for (const { name, endpoint } of healthEndpoints) {
      test(`${name} health check (${endpoint})`, async ({ request }) => {
        test.skip(!isFullStack, 'Requires full Docker Compose stack')

        const response = await request.get(endpoint)

        // Health endpoint should return 200 OK
        expect(response.status()).toBe(200)

        // Response should be JSON
        const contentType = response.headers()['content-type']
        expect(contentType).toContain('application/json')

        // Should have a status field
        const body = await response.json()
        expect(body).toHaveProperty('status')
        expect(body.status).toBe('healthy')
      })
    }
  })

  test.describe('Frontend Static Assets', () => {
    test('index.html is served', async ({ request }) => {
      const response = await request.get('/')
      expect(response.status()).toBe(200)

      const contentType = response.headers()['content-type']
      expect(contentType).toContain('text/html')
    })

    test('main JavaScript bundle loads', async ({ page }) => {
      const jsErrors: string[] = []

      page.on('pageerror', (error) => {
        jsErrors.push(error.message)
      })

      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')

      // React app should mount without JS errors
      expect(jsErrors).toHaveLength(0)

      // App root should exist and have content
      const appRoot = page.locator('#root')
      await expect(appRoot).not.toBeEmpty()
    })

    test('CSS styles are applied', async ({ page }) => {
      await page.goto('/')

      // Check that Tailwind styles are applied (background color should be set)
      const body = page.locator('body')
      const bgColor = await body.evaluate((el) => {
        return window.getComputedStyle(el).backgroundColor
      })

      // Should not be default white/transparent
      expect(bgColor).toBeTruthy()
      expect(bgColor).not.toBe('rgba(0, 0, 0, 0)')
    })
  })

  test.describe('Network Connectivity', () => {
    test('no failed network requests on homepage load', async ({ page }) => {
      const failedRequests: string[] = []

      page.on('requestfailed', (request) => {
        // Ignore external requests (analytics, etc)
        const url = request.url()
        if (!url.includes('localhost') && !url.includes('127.0.0.1')) {
          return
        }
        failedRequests.push(`${request.url()} - ${request.failure()?.errorText}`)
      })

      await page.goto('/')
      await page.waitForLoadState('networkidle')

      // Filter out expected failures (e.g., favicon if not present)
      const criticalFailures = failedRequests.filter(
        (req) => !req.includes('favicon') && !req.includes('.map')
      )

      expect(criticalFailures).toHaveLength(0)
    })

    test('page loads within acceptable time', async ({ page }) => {
      const startTime = Date.now()

      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')

      const loadTime = Date.now() - startTime

      // Page should load within 5 seconds
      expect(loadTime).toBeLessThan(5000)
    })
  })
})
