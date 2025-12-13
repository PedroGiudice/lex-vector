# Performance Considerations

## Current Optimizations

### React Optimizations

#### 1. useMemo for Query Parameters
```typescript
const queryParams: QueryParams = useMemo(
  () => ({
    domain,
    triggerWords: selectedTriggerWords,
    onlyAcordaos,
  }),
  [domain, selectedTriggerWords, onlyAcordaos]
);
```
**Why**: Prevents unnecessary re-renders of child components that depend on query parameters.

#### 2. TanStack Query Caching
```typescript
staleTime: 5 * 60 * 1000, // 5 minutes
```
**Why**: Reduces unnecessary API calls by caching results for 5 minutes.

#### 3. Conditional Query Execution
```typescript
enabled: params.domain !== null || params.triggerWords.length > 0,
```
**Why**: Prevents API calls when no filters are selected.

### Build Optimizations

#### 1. Vite for Fast Development
- Hot Module Replacement (HMR) for instant updates
- Native ES modules for faster cold starts
- Optimized production builds with Rollup

#### 2. Tree Shaking
- Only used Tailwind classes are included in final CSS
- Unused code is eliminated during build

## Performance Metrics (Current Build)

```
dist/index.html                   0.60 kB │ gzip:  0.38 kB
dist/assets/index-DV6zz7B_.css   14.49 kB │ gzip:  3.39 kB
dist/assets/index-CuyDzxN5.js   192.09 kB │ gzip: 61.08 kB
```

**Total Bundle Size**: ~207 KB (uncompressed), ~65 KB (gzipped)

## Recommended Optimizations for Production

### 1. Code Splitting

#### Route-based Splitting
```typescript
// Example for future implementation
const DownloadCenter = lazy(() => import('./components/DownloadCenter'));
const JurisprudenceLab = lazy(() => import('./components/JurisprudenceLab'));
```

**Impact**: Reduces initial bundle size by ~40-60%

#### Component-based Splitting
```typescript
// For large, rarely-used components
const ExportDialog = lazy(() => import('./components/ExportDialog'));
```

**Impact**: Loads heavy components only when needed

### 2. React.memo for Expensive Components

```typescript
// Example for JurisprudenceResultCard
export const JurisprudenceResultCard = React.memo(
  ({ result }: JurisprudenceResultCardProps) => {
    // ... component code
  }
);
```

**When to use**:
- Components that receive complex props
- Components that render frequently
- Components with expensive calculations

**Current candidates**:
- `JurisprudenceResultCard` (rendered in lists)
- `OutcomeBadge` (simple, frequently rendered)

### 3. Virtual Scrolling

For result lists with 100+ items:

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

// Inside component
const virtualizer = useVirtualizer({
  count: results.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 200, // estimated height of each card
});
```

**Impact**: Reduces DOM nodes from 1000+ to ~20

### 4. Image Optimization

If adding images in production:
- Use WebP format with fallbacks
- Implement lazy loading
- Use srcset for responsive images
- Consider using image CDN

### 5. API Response Optimization

```typescript
// Implement pagination
interface PaginatedResults {
  results: JurisprudenceResult[];
  page: number;
  totalPages: number;
  totalResults: number;
}

// Implement infinite scroll
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['jurisprudence', params],
  queryFn: ({ pageParam = 1 }) => fetchJurisprudence(params, pageParam),
  getNextPageParam: (lastPage) => lastPage.nextPage,
});
```

**Impact**: Reduces initial data load by ~80%

### 6. Font Loading Optimization

```html
<!-- Add to index.html -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap">
```

**Impact**: Reduces font loading time by ~30%

### 7. Bundle Analysis

```bash
npm install -D rollup-plugin-visualizer

# Add to vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer';

plugins: [
  react(),
  visualizer({ open: true })
]
```

**Use**: Identify large dependencies to replace or remove

### 8. Service Worker for Offline Support

```typescript
// Register service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}
```

**Impact**: Enables offline functionality and faster repeat visits

## Performance Budget

### Target Metrics (Production)

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| First Contentful Paint | < 1.5s | TBD | ⏳ |
| Largest Contentful Paint | < 2.5s | TBD | ⏳ |
| Time to Interactive | < 3.5s | TBD | ⏳ |
| Cumulative Layout Shift | < 0.1 | TBD | ⏳ |
| First Input Delay | < 100ms | TBD | ⏳ |
| Bundle Size (gzipped) | < 100KB | 65KB | ✅ |

### Testing Tools

1. **Lighthouse** (Chrome DevTools)
   ```bash
   npm install -g lighthouse
   lighthouse http://localhost:3000 --view
   ```

2. **WebPageTest**
   - Test from multiple locations
   - Filmstrip view of loading

3. **Chrome DevTools Performance Tab**
   - Record and analyze runtime performance
   - Identify long tasks

4. **React DevTools Profiler**
   - Identify slow components
   - Analyze render times

## Monitoring in Production

### Recommended Tools

1. **Sentry** - Error tracking and performance monitoring
2. **Google Analytics** - User behavior and page load times
3. **Vercel Analytics** - If deploying on Vercel
4. **New Relic** - Full-stack performance monitoring

### Key Metrics to Track

- Page load time (p50, p75, p95, p99)
- API response times
- Error rates
- Bundle size over time
- Core Web Vitals

## Performance Checklist Before Deployment

- [ ] Run Lighthouse audit (score > 90)
- [ ] Analyze bundle size (< 100KB gzipped target)
- [ ] Implement code splitting for routes
- [ ] Add React.memo to frequently rendered components
- [ ] Configure proper caching headers
- [ ] Compress assets (gzip/brotli)
- [ ] Optimize images (if any)
- [ ] Remove console.logs and debug code
- [ ] Minimize third-party scripts
- [ ] Test on 3G/4G networks
- [ ] Test on low-end devices
- [ ] Set up performance monitoring

## Quick Wins

1. **Enable Brotli compression** on server
   - Impact: 15-20% smaller than gzip

2. **Add `loading="lazy"` to images**
   - Impact: Faster initial page load

3. **Preload critical resources**
   - Impact: Faster First Contentful Paint

4. **Use CDN for static assets**
   - Impact: Faster global delivery

5. **Implement HTTP/2**
   - Impact: Parallel resource loading
