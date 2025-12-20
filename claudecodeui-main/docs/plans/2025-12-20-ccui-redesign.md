# CCui Visual Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform claudecodeui-main to have CCui's visual design while keeping all real functionality (WebSocket, sessions, projects, auth, tool calls, shell, files, source control).

**Architecture:** Create a new CCui-themed design system, then rebuild layout components (IconRail, Header, Sidebar) following CCui patterns, update chat components (messages, thinking, code blocks, input), and wire everything to existing real functionality.

**Tech Stack:** React 18, Tailwind CSS, Prism.js (syntax highlighting), lucide-react, existing WebSocket/auth infrastructure.

---

## Reference: CCui Design Tokens

```css
/* CCui Color Palette */
--ccui-bg-primary: #000000;      /* Pure black */
--ccui-bg-secondary: #050505;    /* Header/sidebar bg */
--ccui-bg-tertiary: #0a0a0a;     /* Input bg */
--ccui-bg-hover: #1a1a1a;        /* Hover states */
--ccui-bg-active: #111111;       /* Active states */

--ccui-border-primary: #1a1a1a;  /* Main borders */
--ccui-border-secondary: #222222; /* Secondary borders */
--ccui-border-tertiary: #333333;  /* Code block borders */

--ccui-text-primary: #e0e0e0;    /* Main text */
--ccui-text-secondary: #888888;  /* Secondary text */
--ccui-text-muted: #666666;      /* Muted text */
--ccui-text-subtle: #444444;     /* Very subtle text */

--ccui-accent: #d97757;          /* Coral accent (Claude brand) */
--ccui-accent-glow: rgba(217, 119, 87, 0.2);

/* Status Colors */
--ccui-success: #22c55e;         /* green-500 */
--ccui-warning: #eab308;         /* yellow-500 */
--ccui-error: #ef4444;           /* red-500 */
--ccui-info: #3b82f6;            /* blue-500 */
```

---

## Phase 1: Design System Foundation

### Task 1.1: Update Tailwind Config with CCui Theme

**Files:**
- Modify: `tailwind.config.js`

**Step 1: Add CCui color palette to Tailwind**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // CCui Design System
        ccui: {
          bg: {
            primary: '#000000',
            secondary: '#050505',
            tertiary: '#0a0a0a',
            hover: '#1a1a1a',
            active: '#111111',
          },
          border: {
            primary: '#1a1a1a',
            secondary: '#222222',
            tertiary: '#333333',
          },
          text: {
            primary: '#e0e0e0',
            secondary: '#888888',
            muted: '#666666',
            subtle: '#444444',
          },
          accent: {
            DEFAULT: '#d97757',
            glow: 'rgba(217, 119, 87, 0.2)',
          },
        },
        // Keep existing for backwards compatibility
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      spacing: {
        'safe-area-inset-bottom': 'env(safe-area-inset-bottom)',
        'mobile-nav': 'var(--mobile-nav-total)',
        'icon-rail': '48px',
        'sidebar': '240px',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'SF Mono', 'Menlo', 'Consolas', 'Liberation Mono', 'monospace'],
      },
      fontSize: {
        'xxs': ['10px', '14px'],
        'xs': ['11px', '16px'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(5px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
```

**Step 2: Verify config is valid**

Run: `bun run build 2>&1 | head -20`
Expected: Build starts without Tailwind config errors

**Step 3: Commit**

```bash
git add tailwind.config.js
git commit -m "feat(design): add CCui color palette to Tailwind config"
```

---

### Task 1.2: Add Prism.js for Syntax Highlighting

**Files:**
- Modify: `index.html`

**Step 1: Add Prism.js CDN to index.html**

Add before `</head>`:

```html
<!-- Prism.js for syntax highlighting -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-typescript.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-jsx.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-tsx.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-css.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-markdown.min.js"></script>
```

**Step 2: Verify Prism loads**

Run: `bun run dev`, open browser console
Expected: `window.Prism` is defined

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat(design): add Prism.js CDN for syntax highlighting"
```

---

### Task 1.3: Add CCui Global Styles

**Files:**
- Modify: `src/index.css`

**Step 1: Add CCui custom scrollbar and animations**

Add at end of file:

```css
/* CCui Custom Scrollbar */
.ccui-scrollbar::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}

.ccui-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.ccui-scrollbar::-webkit-scrollbar-thumb {
  background: #222;
  border-radius: 4px;
}

.ccui-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #333;
}

/* CCui Selection */
.ccui-selection::selection {
  background: rgba(217, 119, 87, 0.3);
}

/* CCui Code Block Overrides for Prism */
.ccui-code pre[class*="language-"] {
  margin: 0 !important;
  padding: 12px !important;
  background: #09090b !important;
  font-size: 11px !important;
  line-height: 1.6 !important;
}

.ccui-code code[class*="language-"] {
  background: transparent !important;
  text-shadow: none !important;
}
```

**Step 2: Verify styles load**

Run: `bun run dev`
Expected: No CSS errors in console

**Step 3: Commit**

```bash
git add src/index.css
git commit -m "feat(design): add CCui global styles and scrollbar"
```

---

## Phase 2: Layout Components

### Task 2.1: Create CCui Header Component

**Files:**
- Create: `src/components/ccui/CCuiHeader.jsx`

**Step 1: Create the header component**

```jsx
import React from 'react';
import { Folder, Cpu, Search, Settings } from 'lucide-react';

/**
 * CCuiHeader - Minimal header with traffic lights, project path, and model selector
 *
 * @param {Object} props
 * @param {string} props.projectPath - Current project path (e.g., "~/project-alpha")
 * @param {string} props.currentModel - Current model name (e.g., "Claude 3.7 Sonnet")
 * @param {Function} props.onSettingsClick - Callback when settings icon clicked
 * @param {Function} props.onSearchClick - Callback when search icon clicked
 */
export default function CCuiHeader({
  projectPath = '~/project',
  currentModel = 'Claude Sonnet',
  onSettingsClick,
  onSearchClick,
}) {
  return (
    <header className="flex-none h-10 bg-ccui-bg-secondary border-b border-ccui-border-primary flex items-center justify-between px-4 z-50 select-none">
      {/* Left: Traffic lights + Project path */}
      <div className="flex items-center gap-3">
        {/* Traffic lights */}
        <div className="flex gap-2 group cursor-pointer">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 group-hover:bg-red-500 border border-red-500/50 transition-colors" />
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 group-hover:bg-yellow-500 border border-yellow-500/50 transition-colors" />
          <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 group-hover:bg-green-500 border border-green-500/50 transition-colors" />
        </div>

        {/* Divider */}
        <div className="h-4 w-px bg-ccui-border-secondary mx-1" />

        {/* Project path */}
        <div className="flex items-center gap-2 text-xs font-medium text-ccui-text-secondary">
          <Folder className="w-3 h-3" />
          <span>{projectPath}</span>
        </div>
      </div>

      {/* Right: Model selector + Actions */}
      <div className="flex items-center gap-4 text-xxs font-mono text-ccui-text-subtle">
        {/* Model selector */}
        <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-ccui-bg-active border border-ccui-border-secondary cursor-pointer hover:border-ccui-accent/50 transition-colors">
          <Cpu className="w-3 h-3 text-ccui-accent" />
          <span className="text-ccui-text-secondary">{currentModel}</span>
        </div>

        {/* Action icons */}
        <div className="flex items-center gap-3">
          <Search
            className="w-3.5 h-3.5 hover:text-ccui-accent cursor-pointer transition-colors"
            onClick={onSearchClick}
          />
          <Settings
            className="w-3.5 h-3.5 hover:text-ccui-accent cursor-pointer transition-colors"
            onClick={onSettingsClick}
          />
        </div>
      </div>
    </header>
  );
}
```

**Step 2: Verify component renders**

Add temporarily to App.jsx and run `bun run dev`
Expected: Header displays with traffic lights, path, model

**Step 3: Commit**

```bash
git add src/components/ccui/CCuiHeader.jsx
git commit -m "feat(ccui): create CCuiHeader component with traffic lights"
```

---

### Task 2.2: Create CCui Icon Rail Component

**Files:**
- Create: `src/components/ccui/CCuiIconRail.jsx`

**Step 1: Create the icon rail component**

```jsx
import React from 'react';
import { MessageSquare, Files, Search, GitBranch, Bug, Settings } from 'lucide-react';

/**
 * CCuiIconRail - Vertical icon rail for view switching
 *
 * @param {Object} props
 * @param {string} props.activeView - Current active view ('chat'|'files'|'search'|'git'|'debug')
 * @param {Function} props.onViewChange - Callback when view changes
 * @param {Function} props.onSettingsClick - Callback when settings clicked
 */
export default function CCuiIconRail({
  activeView = 'chat',
  onViewChange,
  onSettingsClick,
}) {
  const views = [
    { id: 'chat', icon: MessageSquare, label: 'Chat' },
    { id: 'files', icon: Files, label: 'Files' },
    { id: 'search', icon: Search, label: 'Search' },
    { id: 'git', icon: GitBranch, label: 'Git' },
    { id: 'debug', icon: Bug, label: 'Debug' },
  ];

  return (
    <aside className="w-12 bg-ccui-bg-secondary border-r border-ccui-border-primary flex flex-col items-center py-2 z-50">
      {views.map(({ id, icon: Icon, label }) => (
        <button
          key={id}
          onClick={() => onViewChange?.(id)}
          className={`w-full p-3 flex justify-center transition-all duration-200 relative group ${
            activeView === id
              ? 'text-ccui-text-primary'
              : 'text-ccui-text-muted hover:text-ccui-text-secondary'
          }`}
          title={label}
        >
          <Icon className="w-5 h-5" strokeWidth={1.5} />
          {activeView === id && (
            <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-ccui-accent" />
          )}
        </button>
      ))}

      {/* Settings at bottom */}
      <div className="mt-auto mb-2">
        <button
          onClick={onSettingsClick}
          className="w-full p-3 flex justify-center text-ccui-text-muted hover:text-ccui-text-secondary transition-all duration-200"
          title="Settings"
        >
          <Settings className="w-5 h-5" strokeWidth={1.5} />
        </button>
      </div>
    </aside>
  );
}
```

**Step 2: Verify component renders**

Test in isolation with different activeView values
Expected: Icon rail shows with active indicator

**Step 3: Commit**

```bash
git add src/components/ccui/CCuiIconRail.jsx
git commit -m "feat(ccui): create CCuiIconRail component"
```

---

### Task 2.3: Create CCui Sidebar Component

**Files:**
- Create: `src/components/ccui/CCuiSidebar.jsx`

**Step 1: Create the sidebar component with temporal grouping**

```jsx
import React, { useMemo } from 'react';
import { Plus, Edit2, MoreVertical, Clock } from 'lucide-react';

/**
 * Group sessions by temporal categories
 */
function groupSessionsByTime(sessions) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
  const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

  const groups = {
    today: [],
    yesterday: [],
    previousWeek: [],
    older: [],
  };

  sessions.forEach(session => {
    const sessionDate = new Date(session.updatedAt || session.createdAt);
    if (sessionDate >= today) {
      groups.today.push(session);
    } else if (sessionDate >= yesterday) {
      groups.yesterday.push(session);
    } else if (sessionDate >= weekAgo) {
      groups.previousWeek.push(session);
    } else {
      groups.older.push(session);
    }
  });

  return groups;
}

/**
 * CCuiSidebar - Chat-centric sidebar with temporal grouping
 *
 * @param {Object} props
 * @param {Array} props.sessions - Array of session objects
 * @param {string} props.activeSessionId - Currently active session ID
 * @param {Function} props.onSessionSelect - Callback when session selected
 * @param {Function} props.onNewChat - Callback for new chat button
 */
export default function CCuiSidebar({
  sessions = [],
  activeSessionId,
  onSessionSelect,
  onNewChat,
}) {
  const groupedSessions = useMemo(() => groupSessionsByTime(sessions), [sessions]);

  const formatTime = (date) => {
    const d = new Date(date);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderGroup = (label, items) => {
    if (items.length === 0) return null;

    return (
      <div className="mb-4">
        <div className="px-3 mb-1.5 text-xxs font-bold text-ccui-text-subtle uppercase tracking-wider">
          {label}
        </div>
        {items.map(session => (
          <div
            key={session.id}
            onClick={() => onSessionSelect?.(session.id)}
            className={`px-3 py-2 cursor-pointer border-l-2 transition-all ${
              activeSessionId === session.id
                ? 'border-ccui-accent bg-ccui-bg-active'
                : 'border-transparent hover:bg-ccui-bg-hover'
            }`}
          >
            <div className={`text-xs truncate ${
              activeSessionId === session.id
                ? 'text-ccui-text-primary font-medium'
                : 'text-ccui-text-secondary'
            }`}>
              {session.title || session.name || 'New Chat'}
            </div>
            <div className="text-xxs text-ccui-text-subtle mt-0.5 flex items-center gap-1">
              <Clock className="w-2.5 h-2.5" />
              {formatTime(session.updatedAt || session.createdAt)}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <aside className="w-60 bg-ccui-bg-secondary border-r border-ccui-border-primary flex flex-col z-40">
      {/* Header */}
      <div className="h-9 border-b border-ccui-border-primary flex items-center justify-between px-3">
        <span className="text-xxs uppercase font-bold tracking-wider text-ccui-text-muted">
          Chats
        </span>
        <div className="flex gap-1">
          <Edit2 className="w-3.5 h-3.5 text-ccui-text-subtle hover:text-ccui-text-primary cursor-pointer" />
          <MoreVertical className="w-3.5 h-3.5 text-ccui-text-subtle hover:text-ccui-text-primary cursor-pointer" />
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-2">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 bg-ccui-bg-hover hover:bg-ccui-border-secondary text-ccui-text-primary text-xs py-1.5 rounded border border-ccui-border-tertiary transition-colors group"
        >
          <Plus className="w-3.5 h-3.5 text-ccui-text-muted group-hover:text-ccui-accent" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto ccui-scrollbar py-2">
        {renderGroup('Today', groupedSessions.today)}
        {renderGroup('Yesterday', groupedSessions.yesterday)}
        {renderGroup('Previous 7 Days', groupedSessions.previousWeek)}
        {renderGroup('Older', groupedSessions.older)}

        {sessions.length === 0 && (
          <div className="px-3 py-8 text-center text-ccui-text-subtle text-xs">
            No chats yet. Start a new conversation!
          </div>
        )}
      </div>
    </aside>
  );
}
```

**Step 2: Test with mock sessions**

Create test data and verify temporal grouping works
Expected: Sessions grouped correctly by TODAY, YESTERDAY, etc.

**Step 3: Commit**

```bash
git add src/components/ccui/CCuiSidebar.jsx
git commit -m "feat(ccui): create CCuiSidebar with temporal grouping"
```

---

### Task 2.4: Create CCui Status Bar Component

**Files:**
- Create: `src/components/ccui/CCuiStatusBar.jsx`

**Step 1: Create the minimal status bar**

```jsx
import React, { useState, useEffect } from 'react';
import { Activity, Clock } from 'lucide-react';

/**
 * CCuiStatusBar - Minimal status bar like VS Code
 *
 * @param {Object} props
 * @param {boolean} props.isProcessing - Whether Claude is processing
 * @param {number} props.contextPercent - Context usage percentage (0-100)
 * @param {string} props.encoding - File encoding (default: UTF-8)
 * @param {string} props.language - Current language mode
 */
export default function CCuiStatusBar({
  isProcessing = false,
  contextPercent = 0,
  encoding = 'UTF-8',
  language = 'TypeScript',
}) {
  const [elapsed, setElapsed] = useState(0);

  // Timer for session duration
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed(prev => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="h-7 bg-ccui-bg-secondary border-t border-ccui-border-primary flex items-center justify-between px-3 select-none text-xxs font-mono text-ccui-text-muted">
      {/* Left side */}
      <div className="flex items-center gap-4">
        {/* Status indicator */}
        <div className="flex items-center gap-1.5 hover:text-ccui-text-primary cursor-pointer transition-colors">
          <div className={`w-1.5 h-1.5 rounded-full ${
            isProcessing
              ? 'bg-yellow-500 animate-pulse'
              : 'bg-green-500'
          }`} />
          <span>{isProcessing ? 'BUSY' : 'READY'}</span>
        </div>

        {/* Divider */}
        <div className="h-3 w-px bg-ccui-border-secondary" />

        {/* Context usage */}
        <div className="flex items-center gap-1.5">
          <Activity className="w-3 h-3 text-blue-500" />
          <span>{contextPercent}% ctx</span>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        <span>{encoding}</span>
        <span>{language}</span>
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {formatTime(elapsed)}
        </span>
      </div>
    </div>
  );
}
```

**Step 2: Verify timer works**

Run and observe timer counting up
Expected: Timer increments every second, status toggles with prop

**Step 3: Commit**

```bash
git add src/components/ccui/CCuiStatusBar.jsx
git commit -m "feat(ccui): create CCuiStatusBar with minimal design"
```

---

## Phase 3: Chat Components

### Task 3.1: Create CCui Code Block Component (Prism.js)

**Files:**
- Create: `src/components/ccui/CCuiCodeBlock.jsx`

**Step 1: Create code block with Prism.js highlighting**

```jsx
import React, { useState, useCallback, useLayoutEffect, useRef } from 'react';
import { Copy, Check } from 'lucide-react';

/**
 * CCuiCodeBlock - Code block with Prism.js syntax highlighting
 *
 * @param {Object} props
 * @param {string} props.code - The code content
 * @param {string} props.language - Programming language
 * @param {boolean} props.isStreaming - Whether code is still streaming
 */
export default function CCuiCodeBlock({
  code,
  language = 'javascript',
  isStreaming = false,
}) {
  const [copied, setCopied] = useState(false);
  const codeRef = useRef(null);

  // Apply Prism highlighting after render
  useLayoutEffect(() => {
    if (window.Prism && codeRef.current && !isStreaming) {
      window.Prism.highlightElement(codeRef.current);
    }
  }, [code, language, isStreaming]);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [code]);

  return (
    <div className="relative group my-2 rounded-md overflow-hidden border border-ccui-border-tertiary bg-ccui-bg-tertiary shadow-sm">
      {/* Header bar */}
      <div className="flex items-center justify-between px-3 py-1 bg-ccui-bg-hover border-b border-ccui-border-tertiary">
        <div className="flex items-center space-x-2">
          <span className="text-xxs text-ccui-text-secondary font-mono lowercase">
            {language}
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1 text-xxs text-ccui-text-muted hover:text-ccui-text-primary transition-colors"
        >
          {copied ? (
            <Check className="w-3 h-3 text-green-500" />
          ) : (
            <Copy className="w-3 h-3" />
          )}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>

      {/* Code content */}
      <div className="relative ccui-code">
        <pre className="!m-0 !p-3 !bg-[#09090b] text-xs overflow-x-auto ccui-scrollbar font-mono leading-relaxed">
          <code
            ref={codeRef}
            className={`language-${language} !bg-transparent !text-shadow-none`}
          >
            {code}
          </code>
          {isStreaming && (
            <span className="inline-block w-1.5 h-3 bg-ccui-accent align-middle ml-1 animate-pulse" />
          )}
        </pre>
      </div>
    </div>
  );
}
```

**Step 2: Test with various languages**

Render with JS, Python, Bash code samples
Expected: Syntax highlighting applied correctly

**Step 3: Commit**

```bash
git add src/components/ccui/CCuiCodeBlock.jsx
git commit -m "feat(ccui): create CCuiCodeBlock with Prism.js highlighting"
```

---

### Task 3.2: Create CCui Thinking Block Component

**Files:**
- Create: `src/components/ccui/CCuiThinkingBlock.jsx`

**Step 1: Create collapsible thinking block**

```jsx
import React, { useState } from 'react';
import { ChevronRight, ChevronDown, Loader2 } from 'lucide-react';

/**
 * CCuiThinkingBlock - Collapsible thinking/reasoning display
 *
 * @param {Object} props
 * @param {string} props.content - The thinking content
 * @param {boolean} props.isStreaming - Whether still streaming
 * @param {string} props.label - Label (e.g., "Reasoning", "Planning")
 * @param {string} props.duration - Duration string (e.g., "1.2s")
 */
export default function CCuiThinkingBlock({
  content,
  isStreaming = false,
  label = 'Reasoning',
  duration,
}) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="mb-2 group">
      {/* Header - clickable to toggle */}
      <div
        className="flex items-center gap-2 cursor-pointer select-none py-1"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="w-3.5 h-3.5 flex items-center justify-center">
          {isStreaming ? (
            <Loader2 className="w-3 h-3 text-ccui-accent animate-spin" />
          ) : isOpen ? (
            <ChevronDown className="w-3 h-3 text-ccui-text-muted" />
          ) : (
            <ChevronRight className="w-3 h-3 text-ccui-text-muted" />
          )}
        </div>
        <span className={`text-xxs font-mono font-medium tracking-tight ${
          isStreaming ? 'text-ccui-text-primary' : 'text-ccui-text-muted'
        }`}>
          {label}
        </span>
        {duration && (
          <span className="text-xxs text-ccui-text-subtle font-mono ml-auto">
            {duration}
          </span>
        )}
      </div>

      {/* Content - collapsible */}
      {isOpen && (
        <div className="pl-5 pr-2 py-1">
          <div className="text-xs text-ccui-text-muted font-mono border-l border-ccui-border-secondary pl-3 py-1 leading-relaxed">
            {content}
            {isStreaming && (
              <span className="inline-block w-1.5 h-3 bg-ccui-accent ml-1 animate-pulse" />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

**Step 2: Test collapse/expand behavior**

Click header to toggle, verify streaming state
Expected: Toggles smoothly, spinner shows when streaming

**Step 3: Commit**

```bash
git add src/components/ccui/CCuiThinkingBlock.jsx
git commit -m "feat(ccui): create CCuiThinkingBlock collapsible component"
```

---

### Task 3.3: Create CCui Chat Input Component

**Files:**
- Create: `src/components/ccui/CCuiChatInput.jsx`

**Step 1: Create terminal-style input**

```jsx
import React, { useState, useRef, useCallback } from 'react';
import { Terminal, ArrowUp, Command } from 'lucide-react';

/**
 * CCuiChatInput - Terminal-style chat input
 *
 * @param {Object} props
 * @param {Function} props.onSend - Callback when message sent
 * @param {boolean} props.disabled - Whether input is disabled
 * @param {string} props.placeholder - Placeholder text
 * @param {Function} props.onActionsClick - Callback for Actions shortcut
 * @param {Function} props.onHistoryClick - Callback for History shortcut
 */
export default function CCuiChatInput({
  onSend,
  disabled = false,
  placeholder = 'Describe your task or enter a command...',
  onActionsClick,
  onHistoryClick,
}) {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = useCallback(() => {
    if (!value.trim() || disabled) return;
    onSend?.(value.trim());
    setValue('');

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [value, disabled, onSend]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  const handleChange = useCallback((e) => {
    setValue(e.target.value);

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, []);

  return (
    <div className="p-4 bg-gradient-to-t from-black via-black to-transparent z-30">
      <div className="max-w-3xl mx-auto">
        {/* Input container */}
        <div className="relative flex items-start gap-2 p-2.5 bg-ccui-bg-tertiary border border-ccui-border-secondary rounded-lg shadow-2xl focus-within:border-ccui-accent/50 focus-within:bg-[#0c0c0c] transition-all group">
          {/* Terminal icon */}
          <div className="mt-1.5 text-ccui-accent animate-pulse-slow">
            <Terminal className="w-3.5 h-3.5" />
          </div>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="w-full bg-transparent text-ccui-text-primary text-sm font-mono placeholder-ccui-text-subtle focus:outline-none resize-none py-1 ccui-scrollbar disabled:opacity-50"
            rows={1}
            style={{ minHeight: '24px', maxHeight: '120px' }}
            autoFocus
          />

          {/* Send button */}
          <div className="absolute right-2 bottom-2">
            <button
              onClick={handleSubmit}
              disabled={!value.trim() || disabled}
              className={`p-1 rounded transition-all ${
                value.trim() && !disabled
                  ? 'bg-ccui-accent text-white shadow-lg shadow-ccui-accent/20'
                  : 'bg-ccui-bg-hover text-ccui-text-subtle'
              }`}
            >
              <ArrowUp className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Shortcuts hint */}
        <div className="flex justify-center mt-2 gap-4 text-xxs text-ccui-text-subtle font-mono">
          <span
            className="flex items-center gap-1 hover:text-ccui-text-muted cursor-pointer"
            onClick={onActionsClick}
          >
            <Command className="w-3 h-3" /> Actions
          </span>
          <span
            className="flex items-center gap-1 hover:text-ccui-text-muted cursor-pointer"
            onClick={onHistoryClick}
          >
            <ArrowUp className="w-3 h-3" /> History
          </span>
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Test input behavior**

Type, submit with Enter, verify auto-resize
Expected: Input sends on Enter, grows with content

**Step 3: Commit**

```bash
git add src/components/ccui/CCuiChatInput.jsx
git commit -m "feat(ccui): create CCuiChatInput terminal-style component"
```

---

### Task 3.4: Create CCui Message Component

**Files:**
- Create: `src/components/ccui/CCuiMessage.jsx`

**Step 1: Create message component with CCui styling**

```jsx
import React from 'react';
import { Sparkles } from 'lucide-react';
import CCuiCodeBlock from './CCuiCodeBlock';
import CCuiThinkingBlock from './CCuiThinkingBlock';

/**
 * Parse message content and extract code blocks
 */
function parseContent(content) {
  if (!content) return [];

  const parts = content.split(/(```[\s\S]*?```)/g);

  return parts.map((part, index) => {
    if (part.startsWith('```')) {
      const match = part.match(/```(\w*)\n?([\s\S]*?)```/);
      if (match) {
        return {
          type: 'code',
          language: match[1] || 'text',
          content: match[2],
          key: index,
        };
      }
    }
    return {
      type: 'text',
      content: part,
      key: index,
    };
  }).filter(p => p.content.trim());
}

/**
 * CCuiMessage - Single message display
 *
 * @param {Object} props
 * @param {Object} props.message - Message object
 * @param {boolean} props.isStreaming - Whether message is streaming
 */
export default function CCuiMessage({ message, isStreaming = false }) {
  const { role, content, type, label, duration } = message;

  // User message
  if (role === 'user') {
    return (
      <div className="flex flex-col items-end animate-fade-in">
        <div className="bg-ccui-bg-hover border border-ccui-border-secondary text-ccui-text-primary px-3 py-2 rounded-lg shadow-sm max-w-xl text-sm">
          {content}
        </div>
      </div>
    );
  }

  // Assistant message
  const parsedContent = parseContent(content);

  return (
    <div className="flex flex-col items-start animate-fade-in">
      <div className="w-full max-w-3xl pl-1">
        {/* Assistant header */}
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="w-3.5 h-3.5 text-ccui-accent" />
          <span className="text-xxs font-bold text-ccui-text-secondary tracking-wide">
            CLAUDE
          </span>
        </div>

        {/* Thinking block */}
        {type === 'thought' && (
          <CCuiThinkingBlock
            content={content}
            isStreaming={isStreaming}
            label={label}
            duration={duration}
          />
        )}

        {/* Text content with code blocks */}
        {type !== 'thought' && (
          <div className="text-sm leading-relaxed text-[#d1d5db]">
            {parsedContent.map(part => (
              part.type === 'code' ? (
                <CCuiCodeBlock
                  key={part.key}
                  code={part.content}
                  language={part.language}
                  isStreaming={isStreaming}
                />
              ) : (
                <div
                  key={part.key}
                  className="whitespace-pre-wrap mb-1"
                >
                  {part.content}
                  {isStreaming && part.key === parsedContent.length - 1 && (
                    <span className="inline-block w-1.5 h-3 bg-ccui-accent ml-1 animate-pulse" />
                  )}
                </div>
              )
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Test with various message types**

Render user, assistant, thought messages
Expected: Different styles for each role

**Step 3: Commit**

```bash
git add src/components/ccui/CCuiMessage.jsx
git commit -m "feat(ccui): create CCuiMessage component"
```

---

### Task 3.5: Create CCui Components Index

**Files:**
- Create: `src/components/ccui/index.js`

**Step 1: Create barrel export**

```javascript
// CCui Design System Components
export { default as CCuiHeader } from './CCuiHeader';
export { default as CCuiIconRail } from './CCuiIconRail';
export { default as CCuiSidebar } from './CCuiSidebar';
export { default as CCuiStatusBar } from './CCuiStatusBar';
export { default as CCuiCodeBlock } from './CCuiCodeBlock';
export { default as CCuiThinkingBlock } from './CCuiThinkingBlock';
export { default as CCuiChatInput } from './CCuiChatInput';
export { default as CCuiMessage } from './CCuiMessage';
```

**Step 2: Verify imports work**

```javascript
import { CCuiHeader, CCuiSidebar } from './components/ccui';
```

Expected: No import errors

**Step 3: Commit**

```bash
git add src/components/ccui/index.js
git commit -m "feat(ccui): create barrel export for CCui components"
```

---

## Phase 4: Integration

### Task 4.1: Create CCui Main Layout Component

**Files:**
- Create: `src/components/ccui/CCuiLayout.jsx`

**Step 1: Create the main layout integrating all components**

```jsx
import React, { useState, useCallback } from 'react';
import CCuiHeader from './CCuiHeader';
import CCuiIconRail from './CCuiIconRail';
import CCuiSidebar from './CCuiSidebar';
import CCuiStatusBar from './CCuiStatusBar';
import CCuiChatInput from './CCuiChatInput';
import CCuiMessage from './CCuiMessage';

/**
 * CCuiLayout - Main application layout with CCui design
 *
 * This component provides the visual shell. Parent components
 * should pass real data (sessions, messages, WebSocket state).
 *
 * @param {Object} props
 * @param {string} props.projectPath - Current project path
 * @param {string} props.currentModel - Current AI model
 * @param {Array} props.sessions - Session list for sidebar
 * @param {string} props.activeSessionId - Active session ID
 * @param {Array} props.messages - Current chat messages
 * @param {boolean} props.isProcessing - Whether AI is processing
 * @param {number} props.contextPercent - Context usage percentage
 * @param {Function} props.onSessionSelect - Session selection handler
 * @param {Function} props.onNewChat - New chat handler
 * @param {Function} props.onSendMessage - Message send handler
 * @param {Function} props.onSettingsClick - Settings click handler
 * @param {React.ReactNode} props.children - Optional custom content area
 */
export default function CCuiLayout({
  projectPath = '~/project',
  currentModel = 'Claude Sonnet',
  sessions = [],
  activeSessionId,
  messages = [],
  isProcessing = false,
  contextPercent = 0,
  onSessionSelect,
  onNewChat,
  onSendMessage,
  onSettingsClick,
  children,
}) {
  const [sidebarView, setSidebarView] = useState('chat');

  const handleViewChange = useCallback((view) => {
    setSidebarView(view);
  }, []);

  return (
    <div className="flex flex-col h-screen w-full bg-ccui-bg-primary text-ccui-text-primary font-sans overflow-hidden ccui-selection">
      {/* Header */}
      <CCuiHeader
        projectPath={projectPath}
        currentModel={currentModel}
        onSettingsClick={onSettingsClick}
      />

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Icon Rail */}
        <CCuiIconRail
          activeView={sidebarView}
          onViewChange={handleViewChange}
          onSettingsClick={onSettingsClick}
        />

        {/* Sidebar */}
        <CCuiSidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSessionSelect={onSessionSelect}
          onNewChat={onNewChat}
        />

        {/* Main Content */}
        <main className="flex-1 flex flex-col relative bg-ccui-bg-primary">
          {/* Custom content or default chat view */}
          {children || (
            <>
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 md:p-8 pb-32 ccui-scrollbar">
                <div className="max-w-3xl mx-auto space-y-6">
                  {messages.map((msg, index) => (
                    <CCuiMessage
                      key={msg.id || index}
                      message={msg}
                      isStreaming={msg.isStreaming}
                    />
                  ))}
                </div>
              </div>

              {/* Input Area */}
              <CCuiChatInput
                onSend={onSendMessage}
                disabled={isProcessing}
                placeholder={
                  isProcessing
                    ? 'Claude is thinking...'
                    : 'Describe your task or enter a command...'
                }
              />
            </>
          )}
        </main>
      </div>

      {/* Status Bar */}
      <CCuiStatusBar
        isProcessing={isProcessing}
        contextPercent={contextPercent}
      />
    </div>
  );
}
```

**Step 2: Update barrel export**

Add to `src/components/ccui/index.js`:
```javascript
export { default as CCuiLayout } from './CCuiLayout';
```

**Step 3: Commit**

```bash
git add src/components/ccui/CCuiLayout.jsx src/components/ccui/index.js
git commit -m "feat(ccui): create CCuiLayout main shell component"
```

---

### Task 4.2: Create CCui App Wrapper

**Files:**
- Create: `src/CCuiApp.jsx`

**Step 1: Create app wrapper that connects CCui to real functionality**

```jsx
import React, { useState, useEffect, useCallback } from 'react';
import { CCuiLayout } from './components/ccui';
import { useAuth } from './contexts/AuthContext';
import { useWebSocket } from './contexts/WebSocketContext';
import { authenticatedFetch } from './utils/api';

/**
 * CCuiApp - CCui-themed app connected to real backend
 *
 * This wraps CCuiLayout with real WebSocket, session, and auth functionality.
 */
export default function CCuiApp() {
  const { user, isAuthenticated } = useAuth();
  const { ws, isConnected, sendMessage: wsSend } = useWebSocket();

  // State
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [contextPercent, setContextPercent] = useState(0);

  // Load projects on mount
  useEffect(() => {
    if (isAuthenticated) {
      loadProjects();
    }
  }, [isAuthenticated]);

  // Load sessions when project changes
  useEffect(() => {
    if (selectedProject) {
      loadSessions(selectedProject.id);
    }
  }, [selectedProject]);

  // WebSocket message handler
  useEffect(() => {
    if (!ws) return;

    const handleMessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWsMessage(data);
      } catch (e) {
        console.error('WebSocket parse error:', e);
      }
    };

    ws.addEventListener('message', handleMessage);
    return () => ws.removeEventListener('message', handleMessage);
  }, [ws]);

  const loadProjects = async () => {
    try {
      const response = await authenticatedFetch('/api/projects');
      const data = await response.json();
      setProjects(data.projects || []);
      if (data.projects?.length > 0 && !selectedProject) {
        setSelectedProject(data.projects[0]);
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const loadSessions = async (projectId) => {
    try {
      const response = await authenticatedFetch(`/api/sessions?projectId=${projectId}`);
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const handleWsMessage = useCallback((data) => {
    switch (data.type) {
      case 'message':
        setMessages(prev => [...prev, {
          id: data.messageId || Date.now(),
          role: data.role || 'assistant',
          content: data.content || '',
          type: 'text',
          timestamp: new Date(),
        }]);
        break;
      case 'thinking':
        // Add thinking block
        setMessages(prev => [...prev, {
          id: `thinking-${Date.now()}`,
          role: 'assistant',
          content: data.content || 'Thinking...',
          type: 'thought',
          label: 'Reasoning',
          isStreaming: true,
        }]);
        break;
      case 'thinking-complete':
        // Mark thinking as complete
        setMessages(prev => prev.map(m =>
          m.type === 'thought' && m.isStreaming
            ? { ...m, isStreaming: false, duration: data.duration }
            : m
        ));
        break;
      case 'processing-start':
        setIsProcessing(true);
        break;
      case 'processing-complete':
      case 'claude-complete':
        setIsProcessing(false);
        break;
      case 'context-update':
        if (data.percentUsed !== undefined) {
          setContextPercent(Math.round(data.percentUsed));
        }
        break;
      default:
        break;
    }
  }, []);

  const handleSessionSelect = useCallback((sessionId) => {
    setActiveSessionId(sessionId);
    // Load session messages
    loadSessionMessages(sessionId);
  }, []);

  const loadSessionMessages = async (sessionId) => {
    try {
      const response = await authenticatedFetch(`/api/sessions/${sessionId}/messages`);
      const data = await response.json();
      setMessages(data.messages || []);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const handleNewChat = useCallback(() => {
    setActiveSessionId(null);
    setMessages([]);
  }, []);

  const handleSendMessage = useCallback((content) => {
    if (!content.trim()) return;

    // Add user message to UI immediately
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: content.trim(),
      type: 'text',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    // Send via WebSocket
    wsSend?.({
      type: 'chat-message',
      content: content.trim(),
      sessionId: activeSessionId,
      projectId: selectedProject?.id,
      projectName: selectedProject?.name,
    });
  }, [activeSessionId, selectedProject, wsSend]);

  const handleSettingsClick = useCallback(() => {
    // TODO: Open settings panel
    console.log('Settings clicked');
  }, []);

  // Project path for header
  const projectPath = selectedProject
    ? `~/${selectedProject.name}`
    : '~/project';

  return (
    <CCuiLayout
      projectPath={projectPath}
      currentModel="Claude Sonnet"
      sessions={sessions}
      activeSessionId={activeSessionId}
      messages={messages}
      isProcessing={isProcessing}
      contextPercent={contextPercent}
      onSessionSelect={handleSessionSelect}
      onNewChat={handleNewChat}
      onSendMessage={handleSendMessage}
      onSettingsClick={handleSettingsClick}
    />
  );
}
```

**Step 2: Verify integration compiles**

Run: `bun run build`
Expected: No compilation errors

**Step 3: Commit**

```bash
git add src/CCuiApp.jsx
git commit -m "feat(ccui): create CCuiApp wrapper with real backend integration"
```

---

### Task 4.3: Add CCui Route to App

**Files:**
- Modify: `src/App.jsx`

**Step 1: Add CCui route for testing**

Add import at top:
```javascript
import CCuiApp from './CCuiApp';
```

Add route in router configuration (temporary for testing):
```jsx
<Route path="/ccui" element={
  <ProtectedRoute>
    <CCuiApp />
  </ProtectedRoute>
} />
```

**Step 2: Test CCui route**

Navigate to `http://localhost:5173/ccui`
Expected: CCui layout displays with real session data

**Step 3: Commit**

```bash
git add src/App.jsx
git commit -m "feat(ccui): add /ccui route for testing new design"
```

---

## Phase 5: Polish & Finalization

### Task 5.1: Add Tool Call Display to CCui

**Files:**
- Create: `src/components/ccui/CCuiToolCall.jsx`

**Step 1: Create tool call component matching CCui style**

```jsx
import React, { useState } from 'react';
import { Terminal, FileEdit, FileText, ChevronDown, ChevronRight, Check, X } from 'lucide-react';

const TOOL_ICONS = {
  Bash: Terminal,
  Edit: FileEdit,
  Write: FileEdit,
  Read: FileText,
};

const TOOL_COLORS = {
  Bash: 'text-blue-400',
  Edit: 'text-purple-400',
  Write: 'text-purple-400',
  Read: 'text-green-400',
};

/**
 * CCuiToolCall - Display tool invocation in CCui style
 */
export default function CCuiToolCall({
  toolName,
  toolInput,
  toolResult,
  isExpanded: defaultExpanded = false,
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const Icon = TOOL_ICONS[toolName] || Terminal;
  const colorClass = TOOL_COLORS[toolName] || 'text-ccui-text-secondary';

  let parsedInput = toolInput;
  try {
    if (typeof toolInput === 'string') {
      parsedInput = JSON.parse(toolInput);
    }
  } catch {}

  const hasError = toolResult?.isError;

  return (
    <div className="my-2 border border-ccui-border-tertiary rounded-md overflow-hidden bg-ccui-bg-tertiary">
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 py-2 bg-ccui-bg-hover cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 ${colorClass}`} />
          <span className="text-xs font-mono font-medium text-ccui-text-primary">
            {toolName}
          </span>
          {toolResult && (
            hasError ? (
              <X className="w-3 h-3 text-red-500" />
            ) : (
              <Check className="w-3 h-3 text-green-500" />
            )
          )}
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-ccui-text-muted" />
        ) : (
          <ChevronRight className="w-4 h-4 text-ccui-text-muted" />
        )}
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="px-3 py-2 border-t border-ccui-border-tertiary">
          {/* Input preview */}
          {toolName === 'Bash' && parsedInput?.command && (
            <div className="mb-2">
              <div className="text-xxs text-ccui-text-muted mb-1">Command:</div>
              <code className="text-xs font-mono text-green-400 bg-ccui-bg-primary px-2 py-1 rounded block">
                $ {parsedInput.command}
              </code>
            </div>
          )}

          {(toolName === 'Edit' || toolName === 'Write' || toolName === 'Read') && parsedInput?.file_path && (
            <div className="mb-2">
              <div className="text-xxs text-ccui-text-muted mb-1">File:</div>
              <code className="text-xs font-mono text-ccui-accent">
                {parsedInput.file_path}
              </code>
            </div>
          )}

          {/* Result */}
          {toolResult?.content && (
            <div className="mt-2">
              <div className="text-xxs text-ccui-text-muted mb-1">Result:</div>
              <pre className={`text-xs font-mono p-2 rounded overflow-x-auto ccui-scrollbar ${
                hasError
                  ? 'bg-red-950/30 text-red-400 border border-red-900/50'
                  : 'bg-ccui-bg-primary text-ccui-text-secondary'
              }`}>
                {toolResult.content.slice(0, 500)}
                {toolResult.content.length > 500 && '...'}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

**Step 2: Update CCuiMessage to include tool calls**

Add to CCuiMessage.jsx's parseContent to detect tool_use blocks.

**Step 3: Commit**

```bash
git add src/components/ccui/CCuiToolCall.jsx
git commit -m "feat(ccui): create CCuiToolCall component for tool displays"
```

---

### Task 5.2: Make CCui the Default (Optional)

**Files:**
- Modify: `src/App.jsx`

**Step 1: Replace main route with CCui**

Change the main authenticated route to use CCuiApp instead of MainContent.

**Step 2: Test full functionality**

- Login works
- Projects load
- Sessions display with temporal grouping
- Chat messages send/receive
- Tool calls display
- Context percentage updates

**Step 3: Commit**

```bash
git add src/App.jsx
git commit -m "feat(ccui): make CCui design the default interface"
```

---

## Summary

### Files Created (Phase 1-5):
```
src/components/ccui/
├── CCuiHeader.jsx
├── CCuiIconRail.jsx
├── CCuiSidebar.jsx
├── CCuiStatusBar.jsx
├── CCuiCodeBlock.jsx
├── CCuiThinkingBlock.jsx
├── CCuiChatInput.jsx
├── CCuiMessage.jsx
├── CCuiToolCall.jsx
├── CCuiLayout.jsx
└── index.js

src/CCuiApp.jsx
```

### Files Modified:
```
tailwind.config.js      (CCui color palette)
index.html              (Prism.js CDN)
src/index.css           (CCui scrollbar, code styles)
src/App.jsx             (CCui route)
```

### Preserved Functionality:
- ✅ WebSocket real-time communication
- ✅ Session management (create, load, switch)
- ✅ Project management
- ✅ Authentication (AuthContext)
- ✅ Tool call execution
- ✅ Message streaming
- ✅ Context percentage tracking

### Visual Changes:
- ✅ Pure black background (#000000)
- ✅ Coral accent color (#d97757)
- ✅ Traffic light header
- ✅ Temporal session grouping (TODAY, YESTERDAY, etc.)
- ✅ Minimal status bar (READY | ctx% | time)
- ✅ Terminal-style input
- ✅ Prism.js syntax highlighting
- ✅ Collapsible thinking blocks
