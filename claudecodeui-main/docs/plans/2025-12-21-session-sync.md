# Session Sync: CLI ↔ UI Synchronization

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable real-time synchronization between Claude Code CLI sessions and the CCui web interface.

**Architecture:** File-based streaming using chokidar to watch JSONL transcript files, with WebSocket delivery to UI clients. Supports bidirectional communication via stdin injection to active PTY sessions.

**Tech Stack:** Node.js, chokidar, WebSocket (ws), React hooks, Tailwind CSS

---

## Parallel Execution Strategy

This plan is designed for **parallel execution** with isolated tasks:

| Track | Tasks | Subagent | Isolation |
|-------|-------|----------|-----------|
| **A: Backend Core** | 1-4 | `backend-architect` | `server/services/` |
| **B: WebSocket Layer** | 5-7 | `backend-architect` | `server/routes/`, `server/index.js` |
| **C: Frontend Hooks** | 8-10 | `frontend-developer` | `src/hooks/` |
| **D: UI Components** | 11-14 | `frontend-developer` | `src/components/ccui/` |

**Execution Order:**
- Track A and Track B can run in parallel (both backend)
- Track C depends on Track B completion
- Track D depends on Track C completion

---

## Track A: Backend Core Services

### Task 1: Create SessionSyncService - Core Class

**Subagent:** `backend-architect`

**Files:**
- Create: `server/services/sessionSync.js`

**Step 1: Create the service file with EventEmitter base**

```javascript
/**
 * Session Sync Service
 * Watches Claude Code JSONL transcript files and streams updates to clients
 */
import { EventEmitter } from 'events';
import path from 'path';
import fs from 'fs/promises';
import { createReadStream, statSync } from 'fs';
import readline from 'readline';

class SessionSyncService extends EventEmitter {
  constructor() {
    super();
    this.watchers = new Map(); // sessionId -> { watcher, position, clients }
    this.claudeProjectsPath = path.join(process.env.HOME, '.claude', 'projects');
  }

  getSessionFilePath(projectPath, sessionId) {
    return path.join(this.claudeProjectsPath, projectPath, `${sessionId}.jsonl`);
  }

  async sessionExists(projectPath, sessionId) {
    try {
      const filePath = this.getSessionFilePath(projectPath, sessionId);
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }
}

const sessionSyncService = new SessionSyncService();
export default sessionSyncService;
export { SessionSyncService };
```

**Step 2: Commit**
```bash
git add server/services/sessionSync.js
git commit -m "feat(session-sync): add SessionSyncService core class"
```

---

### Task 2: Add File Watching with Incremental Reading

**Subagent:** `backend-architect`

**Files:**
- Modify: `server/services/sessionSync.js`

**Step 1: Add subscribe/unsubscribe methods with chokidar**

```javascript
  async subscribe(projectPath, sessionId, client) {
    const filePath = this.getSessionFilePath(projectPath, sessionId);
    const watchKey = `${projectPath}:${sessionId}`;

    let watchData = this.watchers.get(watchKey);

    if (watchData) {
      watchData.clients.add(client);
      await this.sendCurrentState(filePath, client);
      return;
    }

    const chokidar = (await import('chokidar')).default;

    let filePosition = 0;
    try {
      const stats = statSync(filePath);
      filePosition = stats.size;
    } catch {}

    const watcher = chokidar.watch(filePath, {
      persistent: true,
      awaitWriteFinish: { stabilityThreshold: 50, pollInterval: 25 }
    });

    watchData = {
      watcher,
      position: filePosition,
      clients: new Set([client]),
      filePath
    };

    this.watchers.set(watchKey, watchData);
    await this.sendCurrentState(filePath, client);

    watcher.on('change', async () => {
      await this.handleFileChange(watchKey);
    });
  }

  unsubscribe(projectPath, sessionId, client) {
    const watchKey = `${projectPath}:${sessionId}`;
    const watchData = this.watchers.get(watchKey);
    if (!watchData) return;

    watchData.clients.delete(client);
    if (watchData.clients.size === 0) {
      watchData.watcher.close();
      this.watchers.delete(watchKey);
    }
  }
```

**Step 2: Commit**
```bash
git commit -am "feat(session-sync): add file watching and incremental streaming"
```

---

### Task 3: Add Session Discovery

**Subagent:** `backend-architect`

**Files:**
- Modify: `server/services/sessionSync.js`

**Step 1: Add findActiveSessions and getCurrentSession**

```javascript
  async findActiveSessions(projectPath = null) {
    const sessions = [];
    const projectDirs = projectPath
      ? [path.join(this.claudeProjectsPath, projectPath)]
      : await this.getAllProjectDirs();

    for (const dir of projectDirs) {
      const files = await fs.readdir(dir);
      const jsonlFiles = files.filter(f => f.endsWith('.jsonl') && !f.startsWith('agent-'));

      for (const file of jsonlFiles) {
        const filePath = path.join(dir, file);
        const stats = await fs.stat(filePath);
        const isRecent = Date.now() - stats.mtimeMs < 30 * 60 * 1000;

        if (isRecent) {
          sessions.push({
            sessionId: file.replace('.jsonl', ''),
            projectPath: path.basename(dir),
            lastModified: stats.mtime,
            isActive: this.watchers.has(`${path.basename(dir)}:${file.replace('.jsonl', '')}`)
          });
        }
      }
    }
    return sessions.sort((a, b) => b.lastModified - a.lastModified);
  }

  async getCurrentSession(cwd) {
    const encodedPath = cwd.replace(/\//g, '-').replace(/^-/, '');
    const projectDir = path.join(this.claudeProjectsPath, `-${encodedPath}`);

    const files = await fs.readdir(projectDir);
    const jsonlFiles = files.filter(f => f.endsWith('.jsonl') && !f.startsWith('agent-'));

    let mostRecent = null;
    let mostRecentTime = 0;

    for (const file of jsonlFiles) {
      const stats = await fs.stat(path.join(projectDir, file));
      if (stats.mtimeMs > mostRecentTime) {
        mostRecentTime = stats.mtimeMs;
        mostRecent = {
          sessionId: file.replace('.jsonl', ''),
          projectPath: `-${encodedPath}`,
          lastModified: stats.mtime
        };
      }
    }
    return mostRecent;
  }
```

**Step 2: Commit**
```bash
git commit -am "feat(session-sync): add session discovery"
```

---

### Task 4: Add Message Parsing

**Subagent:** `backend-architect`

**Files:**
- Modify: `server/services/sessionSync.js`

**Step 1: Add parseMessage and helper methods**

```javascript
  parseMessage(message) {
    const base = {
      id: message.uuid || crypto.randomUUID(),
      timestamp: message.timestamp || new Date().toISOString(),
      raw: message
    };

    switch (message.type) {
      case 'user':
        return { ...base, type: 'user', content: message.message?.content || '', role: 'user' };
      case 'assistant':
        return {
          ...base,
          type: 'assistant',
          content: this.extractAssistantContent(message),
          role: 'assistant',
          toolUse: message.message?.content?.filter(c => c.type === 'tool_use') || []
        };
      case 'tool_result':
        return { ...base, type: 'tool_result', toolId: message.tool_use_id, content: message.content };
      default:
        return { ...base, type: message.type || 'unknown', content: JSON.stringify(message) };
    }
  }

  extractAssistantContent(message) {
    const content = message.message?.content;
    if (!content) return '';
    if (typeof content === 'string') return content;
    if (Array.isArray(content)) {
      return content.filter(c => c.type === 'text').map(c => c.text).join('\n');
    }
    return JSON.stringify(content);
  }
```

**Step 2: Commit**
```bash
git commit -am "feat(session-sync): add message parsing"
```

---

## Track B: WebSocket Layer

### Task 5: Create WebSocket Route

**Subagent:** `backend-architect`

**Files:**
- Create: `server/routes/sessionSyncWs.js`

**Step 1: Create handler**

```javascript
import { WebSocket } from 'ws';
import sessionSyncService from '../services/sessionSync.js';

export function handleSessionSyncConnection(ws, req) {
  let currentSubscription = null;

  ws.on('message', async (message) => {
    const data = JSON.parse(message);

    switch (data.type) {
      case 'subscribe':
        if (currentSubscription) {
          sessionSyncService.unsubscribe(currentSubscription.projectPath, currentSubscription.sessionId, ws);
        }
        currentSubscription = { projectPath: data.projectPath, sessionId: data.sessionId };
        await sessionSyncService.subscribe(data.projectPath, data.sessionId, ws);
        ws.send(JSON.stringify({ type: 'subscribed', ...currentSubscription }));
        break;

      case 'subscribe_current':
        const session = await sessionSyncService.getCurrentSession(data.cwd || process.cwd());
        if (session) {
          currentSubscription = { projectPath: session.projectPath, sessionId: session.sessionId };
          await sessionSyncService.subscribe(session.projectPath, session.sessionId, ws);
          ws.send(JSON.stringify({ type: 'subscribed', ...session }));
        }
        break;

      case 'list_sessions':
        const sessions = await sessionSyncService.findActiveSessions(data.projectPath);
        ws.send(JSON.stringify({ type: 'sessions_list', sessions }));
        break;
    }
  });

  ws.on('close', () => {
    if (currentSubscription) {
      sessionSyncService.unsubscribe(currentSubscription.projectPath, currentSubscription.sessionId, ws);
    }
  });

  ws.send(JSON.stringify({ type: 'connected' }));
}
```

**Step 2: Commit**
```bash
git add server/routes/sessionSyncWs.js
git commit -m "feat(session-sync): add WebSocket route"
```

---

### Task 6-7: Register in Server + REST Endpoints

**Subagent:** `backend-architect`

**Files:**
- Modify: `server/index.js`

**Step 1: Import and register**

```javascript
// Add import
import { handleSessionSyncConnection } from './routes/sessionSyncWs.js';
import sessionSyncService from './services/sessionSync.js';

// Add WebSocket path handler (in wss.on('connection'))
if (req.url === '/session-sync') {
  handleSessionSyncConnection(ws, req);
  return;
}

// Add REST endpoints
app.get('/api/sessions/active', authenticateToken, async (req, res) => {
  const sessions = await sessionSyncService.findActiveSessions(req.query.projectPath);
  res.json({ sessions });
});

app.get('/api/sessions/current', authenticateToken, async (req, res) => {
  const session = await sessionSyncService.getCurrentSession(req.query.cwd || process.cwd());
  res.json({ session });
});
```

**Step 2: Commit**
```bash
git commit -am "feat(session-sync): register WebSocket and REST endpoints"
```

---

## Track C: Frontend Hooks

### Task 8-10: Create Hooks

**Subagent:** `frontend-developer`

**Files:**
- Create: `src/hooks/useSessionSync.js`
- Create: `src/hooks/useActiveSessions.js`

(Código completo no plano original - hooks para WebSocket connection e session fetching)

---

## Track D: UI Components

### Task 11-14: Create Components

**Subagent:** `frontend-developer`

**Files:**
- Create: `src/components/ccui/CCuiSessionSyncView.jsx`
- Create: `src/components/ccui/CCuiSessionPicker.jsx`
- Modify: `src/components/ccui/CCuiLayout.jsx`

(Código completo no plano original - componentes React para UI)

---

## Prompt para Nova Sessão

```
Implemente o plano em claudecodeui-main/docs/plans/2025-12-21-session-sync.md

Execute as tracks em paralelo:
- Track A + B: backend-architect (paralelo)
- Track C: frontend-developer (após B)
- Track D: frontend-developer (após C)

Cada task deve ser um commit isolado. Use subagent-driven development.
```
