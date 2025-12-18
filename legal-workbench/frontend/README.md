# Doc Assembler - Template Builder Frontend

React frontend for the legal document template builder. Built with TypeScript, Vite, Tailwind CSS, and Zustand.

## Features

- Drag & drop document upload (.docx files)
- Text selection for field annotation
- Real-time pattern detection
- Dark-themed GitHub-inspired UI
- Toast notifications
- Template saving and management

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling (dark mode only)
- **Zustand** - State management
- **Lucide React** - Icons
- **Axios** - HTTP client

## Prerequisites

- Node.js 20+
- npm or yarn

## Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env
```

## Development

```bash
# Start development server
npm run dev

# Open browser at http://localhost:3000
```

The dev server includes proxy configuration for the backend API at `/api`.

## Building for Production

```bash
# Build the application
npm run build

# Preview the production build
npm run preview
```

## Docker

```bash
# Build Docker image
docker build -t doc-assembler-frontend .

# Run container
docker run -p 3000:3000 doc-assembler-frontend
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/         # Layout components (Header, Sidebar, MainLayout)
│   │   ├── document/       # Document viewer and annotation components
│   │   ├── upload/         # File upload components
│   │   └── ui/            # Reusable UI components (Button, Input, Modal, Toast)
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API service layer
│   ├── store/             # Zustand state management
│   ├── types/             # TypeScript type definitions
│   └── styles/            # Theme configuration
├── public/                # Static assets
└── dist/                  # Production build output
```

## Usage

### 1. Upload Document

Drag and drop a .docx file into the upload zone, or click to browse.

### 2. Create Field Annotations

1. Select text in the document viewer
2. A popup will appear
3. Enter a field name in snake_case (e.g., `nome_autor`, `data_assinatura`)
4. Click "Create Field"

### 3. Manage Annotations

- View all annotations in the right sidebar
- Edit or delete annotations as needed
- Annotations are highlighted in blue in the document

### 4. Save Template

Once you've created all your field annotations, click "Save Template" in the right sidebar.

## API Integration

The frontend expects the following API endpoints:

### POST /api/doc/api/v1/builder/upload
Upload a .docx document.

**Request:** `multipart/form-data` with `file` field
**Response:**
```json
{
  "documentId": "string",
  "textContent": "string",
  "paragraphs": ["string"]
}
```

### POST /api/doc/api/v1/builder/patterns
Detect patterns in text.

**Request:**
```json
{
  "text": "string"
}
```

**Response:**
```json
[
  {
    "pattern": "string",
    "text": "string",
    "start": 0,
    "end": 10,
    "confidence": 0.95
  }
]
```

### POST /api/doc/api/v1/builder/save
Save a template.

**Request:**
```json
{
  "name": "string",
  "documentId": "string",
  "annotations": [
    {
      "fieldName": "string",
      "text": "string",
      "start": 0,
      "end": 10,
      "paragraphIndex": 0
    }
  ]
}
```

**Response:**
```json
{
  "templateId": "string"
}
```

### GET /api/doc/api/v1/builder/templates
List all templates.

**Response:**
```json
[
  {
    "id": "string",
    "name": "string",
    "createdAt": "string",
    "fieldCount": 0
  }
]
```

## Accessibility

- Keyboard navigation support
- ARIA labels on interactive elements
- Focus management for modals
- Semantic HTML structure

## Performance Optimizations

- Code splitting with Vite
- React.memo for expensive components
- Optimized re-renders with Zustand
- Gzip compression in nginx
- Static asset caching

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## License

MIT
