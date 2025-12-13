# Deployment Checklist

## Pre-Deployment

### Code Quality
- [ ] All TypeScript errors resolved
- [ ] All ESLint warnings resolved
- [ ] Remove all console.log statements
- [ ] Remove debug code and comments
- [ ] Code review completed
- [ ] All tests passing
- [ ] Test coverage > 80%

### Build Verification
```bash
# Clean build
rm -rf dist node_modules
npm install
npm run build

# Verify build output
ls -lh dist/
```

- [ ] Build completes without errors
- [ ] Bundle size within budget (< 100KB gzipped)
- [ ] No unused dependencies
- [ ] Source maps generated for debugging

### Environment Configuration

#### Create `.env.production`
```env
VITE_API_BASE_URL=https://api.production.com
VITE_ENVIRONMENT=production
VITE_SENTRY_DSN=your-sentry-dsn
VITE_GA_TRACKING_ID=your-ga-id
```

- [ ] Environment variables configured
- [ ] API endpoints point to production
- [ ] Feature flags set correctly
- [ ] Analytics tracking enabled

### Security

#### Content Security Policy (CSP)
```html
<!-- Add to index.html or server headers -->
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self';
               script-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
               style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
               font-src 'self' https://fonts.gstatic.com;
               connect-src 'self' https://api.production.com">
```

- [ ] CSP headers configured
- [ ] HTTPS enforced
- [ ] CORS policies configured
- [ ] API authentication implemented
- [ ] Rate limiting configured
- [ ] Input validation on all forms
- [ ] XSS protection enabled
- [ ] SQL injection prevention (parameterized queries)

### Performance

- [ ] Lighthouse audit score > 90
- [ ] Core Web Vitals passing
  - LCP < 2.5s
  - FID < 100ms
  - CLS < 0.1
- [ ] Images optimized
- [ ] Code splitting implemented
- [ ] Lazy loading configured
- [ ] Caching strategy defined

### Accessibility

- [ ] WCAG 2.1 AA compliance verified
- [ ] Screen reader testing completed
- [ ] Keyboard navigation tested
- [ ] Color contrast verified
- [ ] Focus management working

### Browser Compatibility

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS 14+)
- [ ] Chrome Mobile (Android 10+)

### Error Tracking & Monitoring

#### Sentry Setup
```typescript
// main.tsx
import * as Sentry from "@sentry/react";

if (import.meta.env.PROD) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.VITE_ENVIRONMENT,
    tracesSampleRate: 1.0,
  });
}
```

- [ ] Sentry (or similar) configured
- [ ] Error boundaries implemented
- [ ] Source maps uploaded to Sentry
- [ ] Performance monitoring enabled

### Analytics

```typescript
// Example: Google Analytics
import ReactGA from 'react-ga4';

if (import.meta.env.PROD) {
  ReactGA.initialize(import.meta.env.VITE_GA_TRACKING_ID);
}
```

- [ ] Analytics tracking configured
- [ ] Key events tracked
- [ ] User flow analytics setup
- [ ] Privacy policy updated

## Deployment

### Build for Production

```bash
# Build the application
npm run build

# Preview the production build locally
npm run preview
```

### Deployment Platforms

#### Option 1: Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

**vercel.json**:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

#### Option 2: Netlify

**netlify.toml**:
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-Content-Type-Options = "nosniff"
    X-XSS-Protection = "1; mode=block"
```

#### Option 3: AWS S3 + CloudFront

```bash
# Install AWS CLI
aws s3 sync dist/ s3://your-bucket-name --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

#### Option 4: Docker

**Dockerfile**:
```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf**:
```nginx
server {
  listen 80;
  server_name _;
  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  # Gzip compression
  gzip on;
  gzip_types text/css application/javascript application/json;
  gzip_min_length 1000;

  # Cache static assets
  location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }
}
```

Build and deploy:
```bash
docker build -t legal-workbench-stj .
docker run -p 80:80 legal-workbench-stj
```

## Post-Deployment

### Immediate Verification

- [ ] Application loads successfully
- [ ] All pages accessible
- [ ] API calls working
- [ ] Authentication working (if applicable)
- [ ] No console errors
- [ ] Analytics tracking events

### Smoke Tests

Test critical user flows:
1. [ ] Load homepage
2. [ ] Apply filters
3. [ ] View SQL preview
4. [ ] Execute query
5. [ ] View results
6. [ ] Apply template
7. [ ] Clear filters

### Monitoring Setup

#### 1. Set Up Alerts

**Sentry Alerts**:
- Error rate > 1% in 5 minutes
- Response time > 3s
- New error types

**Uptime Monitoring** (UptimeRobot, Pingdom):
- Check every 5 minutes
- Alert on 2 consecutive failures

#### 2. Dashboard Setup

Create monitoring dashboard with:
- Request volume
- Error rate
- Response times
- User geography
- Browser distribution
- Device types

### Performance Monitoring

```bash
# Run Lighthouse on production URL
lighthouse https://your-production-url.com --view
```

Track over time:
- [ ] Performance score
- [ ] Accessibility score
- [ ] Best practices score
- [ ] SEO score

### Documentation

- [ ] Update README with production URL
- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Document rollback procedure
- [ ] Update architecture diagrams

## Rollback Procedure

### Quick Rollback

**Vercel/Netlify**:
```bash
# Revert to previous deployment
vercel rollback
# or
netlify rollback
```

**Manual**:
1. Keep previous build artifacts
2. Deploy previous version
3. Verify functionality
4. Clear CDN cache

### Database Rollback (if applicable)

1. [ ] Backup current state
2. [ ] Run rollback migration
3. [ ] Verify data integrity
4. [ ] Test application

## Security Hardening

### Server Headers

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### Rate Limiting

Implement rate limiting on:
- [ ] API endpoints (100 req/min per IP)
- [ ] Login attempts (5 per 15 min)
- [ ] Search queries (20 per min)

### Regular Security Audits

```bash
# NPM audit
npm audit

# Fix vulnerabilities
npm audit fix

# Check for updates
npm outdated
```

Schedule:
- [ ] Weekly dependency updates
- [ ] Monthly security audits
- [ ] Quarterly penetration testing

## Maintenance Plan

### Daily
- [ ] Check error logs
- [ ] Monitor performance metrics
- [ ] Review analytics

### Weekly
- [ ] Review user feedback
- [ ] Check for dependency updates
- [ ] Verify backups

### Monthly
- [ ] Security audit
- [ ] Performance review
- [ ] Update documentation
- [ ] Review and optimize bundle size

### Quarterly
- [ ] Major dependency updates
- [ ] Architecture review
- [ ] Disaster recovery drill
- [ ] User satisfaction survey

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| Tech Lead | TBD | TBD |
| DevOps | TBD | TBD |
| Product Owner | TBD | TBD |
| On-call Engineer | TBD | TBD |

## Success Criteria

Deployment is successful when:
- [ ] Zero critical errors in first 24 hours
- [ ] Performance metrics meet targets
- [ ] User feedback is positive
- [ ] All monitoring systems operational
- [ ] Team trained on production system
- [ ] Documentation complete and accurate
