import { test, expect } from '@playwright/test'

test.describe('Navigation Tests', () => {
  const modules = [
    { id: 'trello', name: 'Trello Command Center', path: '/trello' },
    { id: 'doc-assembler', name: 'Doc Assembler', path: '/doc-assembler' },
    { id: 'stj', name: 'STJ Dados Abertos', path: '/stj' },
    { id: 'text-extractor', name: 'Text Extractor', path: '/text-extractor' },
    { id: 'ledes-converter', name: 'LEDES Converter', path: '/ledes-converter' },
    { id: 'ccui-assistant', name: 'Claude Code', path: '/ccui-assistant' },
  ]

  test.describe('Module Card Navigation', () => {
    for (const module of modules) {
      test(`clicking ${module.name} card navigates to ${module.path}`, async ({ page }) => {
        await page.goto('/')

        // Find the module card by its href - more specific than name matching
        // This avoids matching sidebar links and only matches the main content cards
        const moduleCard = page.locator(`a[href="/${module.id}"]`).filter({ hasText: module.name }).first()
        await expect(moduleCard).toBeVisible()
        await moduleCard.click()

        // Should navigate to the module page
        await expect(page).toHaveURL(module.path)
      })
    }
  })

  test.describe('Direct URL Navigation', () => {
    for (const module of modules) {
      test(`direct navigation to ${module.path} works`, async ({ page }) => {
        await page.goto(module.path)

        // Page should load without redirecting to 404
        await expect(page).toHaveURL(module.path)

        // Loading spinner should disappear (lazy loading complete)
        await page.waitForLoadState('networkidle')
      })
    }
  })

  test('navigating to root shows homepage', async ({ page }) => {
    // First go to a module
    await page.goto('/trello')
    await expect(page).toHaveURL('/trello')

    // Then navigate back to root
    await page.goto('/')
    await expect(page).toHaveURL('/')

    // Homepage content should be visible
    await expect(page.getByRole('heading', { name: 'Bem-vindo ao Legal Workbench' })).toBeVisible()
  })

  test('browser back button works correctly', async ({ page }) => {
    // Start at homepage
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Navigate to a module using the main content card
    const trelloCard = page.locator('a[href="/trello"]').filter({ hasText: 'Trello Command Center' }).first()
    await trelloCard.click()
    await expect(page).toHaveURL('/trello')

    // Go back using browser back button
    await page.goBack()
    await expect(page).toHaveURL('/')

    // Homepage content should be visible
    await expect(page.getByRole('heading', { name: 'Bem-vindo ao Legal Workbench' })).toBeVisible()
  })

  test('browser forward button works correctly', async ({ page }) => {
    // Navigate from home to module
    await page.goto('/')
    const docCard = page.locator('a[href="/doc-assembler"]').filter({ hasText: 'Doc Assembler' }).first()
    await docCard.click()
    await expect(page).toHaveURL('/doc-assembler')

    // Go back to homepage
    await page.goBack()
    await expect(page).toHaveURL('/')

    // Go forward to module
    await page.goForward()
    await expect(page).toHaveURL('/doc-assembler')
  })

  test('multiple sequential navigations work', async ({ page }) => {
    await page.goto('/')

    // Navigate through multiple modules
    const navigationSequence = ['/trello', '/doc-assembler', '/stj', '/']

    for (const path of navigationSequence) {
      await page.goto(path)
      await expect(page).toHaveURL(path)
      await page.waitForLoadState('networkidle')
    }
  })
})

test.describe('CCui V2 Navigation', () => {
  test('ccui-v2 module is accessible', async ({ page }) => {
    await page.goto('/ccui-v2')
    await expect(page).toHaveURL('/ccui-v2')
    await page.waitForLoadState('networkidle')
  })
})
