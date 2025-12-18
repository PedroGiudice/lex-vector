# Quick Start Guide

Get the Doc Assembler Template Builder frontend up and running in minutes.

## Prerequisites

- Node.js 20+ installed
- npm or yarn
- Backend API running at `http://localhost:8000` (or configure via .env)

## Installation

```bash
# Navigate to frontend directory
cd /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/legal-workbench/frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# (Optional) Edit .env to point to your backend
# VITE_API_BASE_URL=http://localhost:8000
```

## Development

```bash
# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

## Using the Application

### Step 1: Upload a Document

1. Look for the upload zone in the left sidebar
2. Drag and drop a .docx file OR click to browse
3. Wait for the upload to complete
4. The document will appear in the center viewer

### Step 2: Create Field Annotations

1. In the document viewer, select any text with your mouse
2. A popup will appear
3. Enter a field name in snake_case (e.g., `nome_autor`, `data_contrato`)
4. Click "Create Field"
5. The text will be highlighted in blue

### Step 3: Manage Annotations

1. View all annotations in the right sidebar
2. Each annotation shows:
   - Field name (in blue)
   - Original text snippet
   - Paragraph number
3. Click the trash icon to delete an annotation

### Step 4: Save Template

1. Once you've created all your annotations
2. Click "Save Template" in the right sidebar
3. Enter a template name (e.g., "Contrato de Prestação de Serviços")
4. Click "Save"
5. Your template is now saved to the backend

## Keyboard Shortcuts

- `Tab` / `Shift+Tab` - Navigate between elements
- `Escape` - Close modals/popups
- `Enter` - Submit forms/activate buttons

## Common Issues

### Port Already in Use

If port 3000 is already in use, edit `vite.config.ts`:

```typescript
server: {
  port: 3001, // Change to any available port
  // ...
}
```

### API Connection Issues

1. Verify backend is running at `http://localhost:8000`
2. Check browser console for CORS errors
3. Verify `.env` has correct `VITE_API_BASE_URL`
4. Check `vite.config.ts` proxy configuration

### Build Errors

If you encounter TypeScript errors during build:

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install

# Try building again
npm run build
```

## Testing

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test -- --watch

# Run tests with coverage
npm run test -- --coverage
```

## Building for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build locally
npm run preview
```

## Docker

```bash
# Build Docker image
docker build -t doc-assembler-frontend .

# Run container
docker run -p 3000:3000 doc-assembler-frontend

# Check health
curl http://localhost:3000/health
```

## Project Structure

```
frontend/
├── src/
│   ├── components/        # React components
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API integration
│   ├── store/            # Zustand state management
│   └── types/            # TypeScript definitions
├── public/               # Static assets
└── dist/                 # Production build (after npm run build)
```

## Next Steps

- Read the full [README.md](./README.md) for detailed documentation
- Review [DEPLOYMENT.md](./DEPLOYMENT.md) before deploying to production
- Check [ACCESSIBILITY.md](./ACCESSIBILITY.md) for accessibility features
- See [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) for technical details

## Getting Help

If you encounter issues:

1. Check the browser console for errors
2. Check the network tab for API request failures
3. Verify all environment variables are set correctly
4. Ensure the backend API is running and accessible
5. Review the documentation files in this directory

## Development Tips

- The app uses hot module replacement (HMR) - changes appear instantly
- TypeScript errors will show in the terminal and browser
- Toast notifications appear in the top-right corner
- Use React DevTools browser extension for debugging
- Use Zustand DevTools for state inspection

---

Happy coding!
