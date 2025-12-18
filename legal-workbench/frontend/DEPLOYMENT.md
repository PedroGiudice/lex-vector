# Deployment Checklist

Complete this checklist before deploying to production.

## Pre-Deployment

### Code Quality
- [ ] All TypeScript errors resolved (`npm run build` succeeds)
- [ ] ESLint warnings addressed (`npm run lint` passes)
- [ ] All tests passing (`npm run test`)
- [ ] Code reviewed by at least one other developer
- [ ] No console.log statements in production code
- [ ] No hardcoded API URLs or secrets

### Testing
- [ ] Unit tests coverage > 80%
- [ ] Integration tests pass
- [ ] Manual testing completed for all features
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile responsiveness verified
- [ ] Accessibility audit completed (WCAG 2.1 AA)

### Security
- [ ] Dependencies updated to latest secure versions
- [ ] No known vulnerabilities (`npm audit`)
- [ ] API keys and secrets in environment variables
- [ ] CORS configuration reviewed
- [ ] Content Security Policy headers configured
- [ ] HTTPS enforced

### Performance
- [ ] Lighthouse score > 90 for Performance
- [ ] Bundle size analyzed and optimized
- [ ] Images optimized
- [ ] Code splitting implemented
- [ ] Lazy loading for routes
- [ ] Service worker configured (if using PWA)

### Documentation
- [ ] README updated with latest instructions
- [ ] API documentation current
- [ ] Environment variables documented
- [ ] Deployment process documented
- [ ] Rollback procedure documented

## Build

```bash
# Clean install dependencies
rm -rf node_modules package-lock.json
npm install

# Run tests
npm run test

# Run linter
npm run lint

# Build for production
npm run build

# Test production build locally
npm run preview
```

## Docker Build

```bash
# Build Docker image
docker build -t doc-assembler-frontend:latest .

# Test Docker container locally
docker run -p 3000:3000 doc-assembler-frontend:latest

# Verify health check
curl http://localhost:3000/health
```

## Deployment

### Environment Variables

Ensure these are set in your production environment:

```bash
VITE_API_BASE_URL=https://api.production.com
```

### Health Checks

- [ ] `/health` endpoint returns 200
- [ ] Application loads without errors
- [ ] API integration working
- [ ] Static assets loading correctly

### Monitoring

- [ ] Error tracking configured (e.g., Sentry)
- [ ] Analytics configured (e.g., Google Analytics)
- [ ] Performance monitoring enabled
- [ ] Uptime monitoring configured

## Post-Deployment

- [ ] Smoke tests pass in production
- [ ] Critical user flows verified
- [ ] Performance metrics within acceptable range
- [ ] No errors in browser console
- [ ] No errors in server logs
- [ ] Team notified of deployment
- [ ] Documentation updated with deployment date

## Rollback Plan

If issues are detected:

1. Immediately switch traffic to previous version
2. Investigate root cause
3. Document issue
4. Fix and redeploy

### Rollback Commands

```bash
# Docker rollback
docker tag doc-assembler-frontend:previous doc-assembler-frontend:latest
docker push doc-assembler-frontend:latest

# Restart services
docker compose up -d
```

## Performance Targets

- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.0s
- Largest Contentful Paint: < 2.5s
- Cumulative Layout Shift: < 0.1
- Total Bundle Size: < 500KB (gzipped)

## Browser Support

Minimum versions:
- Chrome/Edge: last 2 versions
- Firefox: last 2 versions
- Safari: last 2 versions

## Accessibility Requirements

- WCAG 2.1 Level AA compliance
- Keyboard navigation fully functional
- Screen reader compatible
- Sufficient color contrast ratios
- Focus indicators visible
- ARIA labels on interactive elements
