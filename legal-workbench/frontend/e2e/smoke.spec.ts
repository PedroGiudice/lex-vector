import { test, expect } from '@playwright/test'

test.describe('Smoke Tests', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/')

    // Page should have loaded without errors
    await expect(page).toHaveTitle(/Legal Workbench|Doc Assembler/)

    // Main heading (h1) should be visible - use first() for exact match
    await expect(page.getByRole('heading', { name: 'Legal Workbench', exact: true, level: 1 })).toBeVisible()
  })

  test('homepage displays welcome section', async ({ page }) => {
    await page.goto('/')

    // Welcome section should be present
    await expect(page.getByRole('heading', { name: 'Bem-vindo ao Legal Workbench' })).toBeVisible()
    await expect(page.getByText(/Selecione um módulo abaixo para começar/i)).toBeVisible()
  })

  test('homepage displays all module cards', async ({ page }) => {
    await page.goto('/')

    // All 6 main modules should be visible as h3 headings in module cards
    const expectedModules = [
      'Trello Command Center',
      'Doc Assembler',
      'STJ Dados Abertos',
      'Text Extractor',
      'LEDES Converter',
      'Claude Code',
    ]

    for (const moduleName of expectedModules) {
      await expect(page.getByRole('heading', { name: moduleName, level: 3 })).toBeVisible()
    }
  })

  test('homepage displays stats section', async ({ page }) => {
    await page.goto('/')

    // Stats section should show module count and version
    await expect(page.getByText('6')).toBeVisible()
    await expect(page.getByText(/Módulos ativos/i)).toBeVisible()
    await expect(page.getByText('v1.0')).toBeVisible()
    await expect(page.getByText('React')).toBeVisible()
  })

  test('page has no console errors on load', async ({ page }) => {
    const consoleErrors: string[] = []

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text())
      }
    })

    await page.goto('/')

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle')

    // Filter out known non-critical errors (e.g., favicon, analytics)
    const criticalErrors = consoleErrors.filter(
      (error) =>
        !error.includes('favicon') &&
        !error.includes('analytics') &&
        !error.includes('Failed to load resource')
    )

    expect(criticalErrors).toHaveLength(0)
  })
})
