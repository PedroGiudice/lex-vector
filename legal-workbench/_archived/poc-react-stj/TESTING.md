# Testing Strategy

## Testing Philosophy

1. **Test behavior, not implementation**
2. **Write tests that give confidence**
3. **Avoid testing framework internals**
4. **Test from the user's perspective**

## Test Structure

### Unit Tests
Test individual components and functions in isolation.

**Location**: `*.test.tsx` next to component files

**Example**: `OutcomeBadge.test.tsx` ✅ (Already implemented)

### Integration Tests
Test how components work together.

**Example**:
```typescript
// STJQueryBuilder.integration.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { STJQueryBuilder } from './STJQueryBuilder';

describe('STJQueryBuilder Integration', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  it('updates SQL preview when filters change', async () => {
    const user = userEvent.setup();
    render(<STJQueryBuilder />, { wrapper });

    // Initial state - no filters
    expect(screen.getByText(/SELECT \*/)).toBeInTheDocument();

    // Select domain
    const domainSelect = screen.getByRole('combobox');
    await user.selectOptions(domainSelect, 'Direito Civil');

    // SQL preview should update
    await waitFor(() => {
      expect(screen.getByText(/domain = 'Direito Civil'/)).toBeInTheDocument();
    });
  });

  it('fetches results when filters are applied', async () => {
    const user = userEvent.setup();
    render(<STJQueryBuilder />, { wrapper });

    // Apply filter
    const domainSelect = screen.getByRole('combobox');
    await user.selectOptions(domainSelect, 'Direito Civil');

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText(/RESULTADOS/)).toBeInTheDocument();
    });

    // Should show result cards
    expect(screen.getByText(/REsp/)).toBeInTheDocument();
  });

  it('applies template and updates filters', async () => {
    const user = userEvent.setup();
    render(<STJQueryBuilder />, { wrapper });

    // Click template button
    const templateButton = screen.getByRole('button', {
      name: /Recursos Repetitivos/,
    });
    await user.click(templateButton);

    // Should update toggle
    const toggle = screen.getByRole('checkbox');
    expect(toggle).toBeChecked();
  });
});
```

### End-to-End Tests
Test complete user flows using Playwright.

**Example**:
```typescript
// e2e/jurisprudence-search.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Jurisprudence Search Flow', () => {
  test('user can search for jurisprudence', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Page should load
    await expect(page.locator('h1')).toContainText('STJ JURISPRUDENCE LAB');

    // Select domain
    await page.selectOption('select', 'Direito Civil');

    // Select trigger words
    await page.click('text=Dano Moral');
    await page.click('text=Lucros Cessantes');

    // SQL preview should update
    await expect(page.locator('pre code')).toContainText('Dano Moral');

    // Results should appear
    await expect(page.locator('[class*="card-terminal"]').first())
      .toBeVisible();

    // Should show outcome badges
    await expect(page.locator('text=PROVIDO')).toBeVisible();
  });

  test('user can apply template', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Click template
    await page.click('text=Recursos Repetitivos');

    // Toggle should be active
    const toggle = page.locator('input[type="checkbox"]');
    await expect(toggle).toBeChecked();

    // Badge should appear
    await expect(page.locator('text=FILTRO ATIVO')).toBeVisible();
  });

  test('user can clear filters', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Apply filters
    await page.selectOption('select', 'Direito Penal');
    await page.click('text=Habeas Corpus');

    // Clear filters
    await page.click('text=Limpar Filtros');

    // Filters should reset
    const select = page.locator('select');
    await expect(select).toHaveValue('');

    // Trigger word should not be selected
    const triggerWord = page.locator('text=Habeas Corpus');
    await expect(triggerWord).not.toHaveClass(/bg-terminal-accent/);
  });
});
```

## Test Coverage Goals

| Type | Target | Priority |
|------|--------|----------|
| Statements | > 80% | High |
| Branches | > 75% | High |
| Functions | > 80% | High |
| Lines | > 80% | High |

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test OutcomeBadge.test.tsx

# Run E2E tests (after setup)
npx playwright test
```

## Mock Data Strategy

### API Mocking

For development and testing, use mock data:

```typescript
// src/utils/mockData.ts
export const MOCK_RESULTS: JurisprudenceResult[] = [...];
```

For production-like testing, use MSW (Mock Service Worker):

```typescript
// src/mocks/handlers.ts
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/jurisprudence', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ results: MOCK_RESULTS })
    );
  }),
];
```

```typescript
// src/mocks/browser.ts
import { setupWorker } from 'msw';
import { handlers } from './handlers';

export const worker = setupWorker(...handlers);
```

## Test Utilities

### Custom Render Function

```typescript
// src/utils/test-utils.tsx
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

### Custom Matchers

```typescript
// src/setupTests.ts
import '@testing-library/jest-dom';

// Add custom matchers if needed
expect.extend({
  toBeValidSQL(received: string) {
    const pass = received.includes('SELECT') && received.includes('FROM');
    return {
      pass,
      message: () =>
        pass
          ? `expected ${received} not to be valid SQL`
          : `expected ${received} to be valid SQL`,
    };
  },
});
```

## Accessibility Testing

```typescript
// Install
npm install -D jest-axe

// Test
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

it('should have no accessibility violations', async () => {
  const { container } = render(<STJQueryBuilder />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

## Visual Regression Testing

```typescript
// Using Playwright for visual testing
test('jurisprudence lab visual', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await expect(page).toHaveScreenshot('jurisprudence-lab.png');
});
```

## Performance Testing

```typescript
// Test render performance
import { render } from '@testing-library/react';
import { performance } from 'perf_hooks';

it('renders large result set efficiently', () => {
  const start = performance.now();

  render(<STJQueryBuilder />);

  const end = performance.now();
  const renderTime = end - start;

  expect(renderTime).toBeLessThan(100); // Should render in < 100ms
});
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run tests
        run: npm test -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

      - name: Build
        run: npm run build
```

## Best Practices

### DO ✅

1. **Test user behavior**
   ```typescript
   it('shows results when search is executed', async () => {
     // Test what user sees, not internal state
   });
   ```

2. **Use semantic queries**
   ```typescript
   screen.getByRole('button', { name: /search/i });
   screen.getByLabelText(/domain/i);
   ```

3. **Wait for async operations**
   ```typescript
   await waitFor(() => {
     expect(screen.getByText(/results/i)).toBeInTheDocument();
   });
   ```

4. **Test error states**
   ```typescript
   it('shows error message when API fails', async () => {
     // Mock API failure
     // Verify error message appears
   });
   ```

5. **Clean up after tests**
   ```typescript
   afterEach(() => {
     queryClient.clear();
     cleanup();
   });
   ```

### DON'T ❌

1. **Don't test implementation details**
   ```typescript
   // Bad
   expect(component.state.loading).toBe(true);

   // Good
   expect(screen.getByRole('progressbar')).toBeInTheDocument();
   ```

2. **Don't use fragile selectors**
   ```typescript
   // Bad
   container.querySelector('.card-terminal > div:nth-child(2)');

   // Good
   screen.getByRole('heading', { level: 2 });
   ```

3. **Don't forget to await async operations**
   ```typescript
   // Bad
   userEvent.click(button);
   expect(screen.getByText(/results/i)).toBeInTheDocument();

   // Good
   await userEvent.click(button);
   await waitFor(() => {
     expect(screen.getByText(/results/i)).toBeInTheDocument();
   });
   ```

## Test Checklist

Before merging:
- [ ] All tests pass
- [ ] Coverage meets minimum threshold (80%)
- [ ] No console errors in tests
- [ ] Accessibility tests pass
- [ ] E2E critical paths covered
- [ ] CI pipeline green
- [ ] Test names are descriptive
- [ ] Edge cases tested
- [ ] Error states tested
- [ ] Loading states tested
