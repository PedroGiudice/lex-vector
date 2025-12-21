/**
 * Session Sync Service
 * Watches Claude Code JSONL transcript files and streams updates to WebSocket clients
 *
 * Architecture:
 * - Uses chokidar for file watching with awaitWriteFinish for stability
 * - Tracks file position for incremental reading (only new content)
 * - Manages multiple clients per session with efficient resource sharing
 * - Emits events to subscribed WebSocket clients
 *
 * Session Discovery:
 * - Scans ~/.claude/projects/ for recent JSONL files
 * - Identifies active sessions (modified within 30 minutes)
 * - Supports current session detection from CWD
 */

import { EventEmitter } from 'events';
import path from 'path';
import fs from 'fs/promises';
import { createReadStream, statSync } from 'fs';
import readline from 'readline';
import crypto from 'crypto';
import { WebSocket } from 'ws';

class SessionSyncService extends EventEmitter {
  constructor() {
    super();

    // Map of watchKey -> { watcher, position, clients, filePath }
    // watchKey format: "projectPath:sessionId"
    this.watchers = new Map();

    // Claude Code stores projects in ~/.claude/projects/
    this.claudeProjectsPath = path.join(process.env.HOME, '.claude', 'projects');

    console.log('[SessionSync] Service initialized, watching:', this.claudeProjectsPath);
  }

  /**
   * Get the full path to a session's JSONL file
   * @param {string} projectPath - Encoded project path (e.g., "-home-user-project")
   * @param {string} sessionId - Session ID (timestamp-based)
   * @returns {string} Full path to JSONL file
   */
  getSessionFilePath(projectPath, sessionId) {
    return path.join(this.claudeProjectsPath, projectPath, `${sessionId}.jsonl`);
  }

  /**
   * Check if a session file exists
   * @param {string} projectPath - Encoded project path
   * @param {string} sessionId - Session ID
   * @returns {Promise<boolean>} True if session exists
   */
  async sessionExists(projectPath, sessionId) {
    try {
      const filePath = this.getSessionFilePath(projectPath, sessionId);
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Subscribe a WebSocket client to a session's updates
   * Initializes file watcher if first client, or reuses existing watcher
   * Sends current file state to client upon subscription
   *
   * @param {string} projectPath - Encoded project path
   * @param {string} sessionId - Session ID
   * @param {WebSocket} client - WebSocket client to subscribe
   */
  async subscribe(projectPath, sessionId, client) {
    const filePath = this.getSessionFilePath(projectPath, sessionId);
    const watchKey = `${projectPath}:${sessionId}`;

    console.log(`[SessionSync] Subscribing client to ${watchKey}`);

    // Check if already watching this session
    let watchData = this.watchers.get(watchKey);

    if (watchData) {
      // Add client to existing watcher
      watchData.clients.add(client);
      console.log(`[SessionSync] Added client to existing watcher (${watchData.clients.size} total clients)`);

      // Send current state to new client
      await this.sendCurrentState(filePath, client);
      return;
    }

    // Import chokidar dynamically
    const chokidar = (await import('chokidar')).default;

    // Initialize file position to current size (start at end)
    let filePosition = 0;
    try {
      const stats = statSync(filePath);
      filePosition = stats.size;
      console.log(`[SessionSync] Initializing watcher at position ${filePosition}`);
    } catch (err) {
      console.log(`[SessionSync] File not yet created: ${filePath}`);
    }

    // Create new file watcher
    const watcher = chokidar.watch(filePath, {
      persistent: true,
      ignoreInitial: true,
      awaitWriteFinish: {
        stabilityThreshold: 50,  // Wait 50ms after last write
        pollInterval: 25         // Poll every 25ms
      }
    });

    // Store watcher data
    watchData = {
      watcher,
      position: filePosition,
      clients: new Set([client]),
      filePath
    };

    this.watchers.set(watchKey, watchData);

    // Send current file state to client
    await this.sendCurrentState(filePath, client);

    // Handle file changes
    watcher.on('change', async () => {
      await this.handleFileChange(watchKey);
    });

    // Handle watcher errors
    watcher.on('error', (error) => {
      console.error(`[SessionSync] Watcher error for ${watchKey}:`, error);
    });

    console.log(`[SessionSync] Created new watcher for ${watchKey}`);
  }

  /**
   * Unsubscribe a WebSocket client from a session
   * Closes watcher if no more clients are subscribed
   *
   * @param {string} projectPath - Encoded project path
   * @param {string} sessionId - Session ID
   * @param {WebSocket} client - WebSocket client to unsubscribe
   */
  unsubscribe(projectPath, sessionId, client) {
    const watchKey = `${projectPath}:${sessionId}`;
    const watchData = this.watchers.get(watchKey);

    if (!watchData) {
      return;
    }

    watchData.clients.delete(client);
    console.log(`[SessionSync] Client unsubscribed from ${watchKey} (${watchData.clients.size} remaining)`);

    // Clean up watcher if no clients remain
    if (watchData.clients.size === 0) {
      watchData.watcher.close();
      this.watchers.delete(watchKey);
      console.log(`[SessionSync] Closed watcher for ${watchKey}`);
    }
  }

  /**
   * Handle file change events - read new content and broadcast to clients
   * Implements incremental reading by tracking file position
   *
   * @param {string} watchKey - Watch key (projectPath:sessionId)
   */
  async handleFileChange(watchKey) {
    const watchData = this.watchers.get(watchKey);
    if (!watchData) return;

    try {
      const stats = statSync(watchData.filePath);
      const newSize = stats.size;

      // Only read if file has grown
      if (newSize <= watchData.position) {
        return;
      }

      // Read only the new content
      const newContent = await this.readFileFromPosition(watchData.filePath, watchData.position, newSize);

      // Update position
      watchData.position = newSize;

      // Parse and broadcast new messages
      const lines = newContent.split('\n').filter(line => line.trim());

      for (const line of lines) {
        try {
          const rawMessage = JSON.parse(line);
          const parsedMessage = this.parseMessage(rawMessage);

          // Broadcast to all subscribed clients
          this.broadcastToClients(watchData.clients, {
            type: 'session_update',
            message: parsedMessage
          });
        } catch (parseError) {
          console.error('[SessionSync] Failed to parse message:', parseError);
        }
      }

    } catch (error) {
      console.error(`[SessionSync] Error handling file change for ${watchKey}:`, error);
    }
  }

  /**
   * Read file content from specific byte position
   *
   * @param {string} filePath - Path to file
   * @param {number} startPosition - Start byte position
   * @param {number} endPosition - End byte position
   * @returns {Promise<string>} File content
   */
  async readFileFromPosition(filePath, startPosition, endPosition) {
    return new Promise((resolve, reject) => {
      const chunks = [];
      const stream = createReadStream(filePath, {
        start: startPosition,
        end: endPosition - 1
      });

      stream.on('data', chunk => chunks.push(chunk));
      stream.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
      stream.on('error', reject);
    });
  }

  /**
   * Send current file state to a client
   * Reads entire file and sends all messages
   *
   * @param {string} filePath - Path to JSONL file
   * @param {WebSocket} client - WebSocket client
   */
  async sendCurrentState(filePath, client) {
    try {
      const fileStream = createReadStream(filePath);
      const rl = readline.createInterface({
        input: fileStream,
        crlfDelay: Infinity
      });

      const messages = [];

      for await (const line of rl) {
        if (line.trim()) {
          try {
            const rawMessage = JSON.parse(line);
            const parsedMessage = this.parseMessage(rawMessage);
            messages.push(parsedMessage);
          } catch (parseError) {
            console.error('[SessionSync] Failed to parse line:', parseError);
          }
        }
      }

      // Send all messages at once
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify({
          type: 'session_state',
          messages
        }));
        console.log(`[SessionSync] Sent ${messages.length} messages to client`);
      }

    } catch (error) {
      if (error.code !== 'ENOENT') {
        console.error('[SessionSync] Error sending current state:', error);
      }
      // Send empty state if file doesn't exist yet
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify({
          type: 'session_state',
          messages: []
        }));
      }
    }
  }

  /**
   * Broadcast message to all clients in a set
   *
   * @param {Set<WebSocket>} clients - Set of WebSocket clients
   * @param {Object} message - Message to broadcast
   */
  broadcastToClients(clients, message) {
    const messageStr = JSON.stringify(message);

    clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(messageStr);
      }
    });
  }

  /**
   * Parse a JSONL message into a standardized format
   * Handles different message types: user, assistant, tool_result
   *
   * @param {Object} message - Raw JSONL message
   * @returns {Object} Parsed message with type, content, timestamp
   */
  parseMessage(message) {
    const base = {
      id: message.uuid || crypto.randomUUID(),
      timestamp: message.timestamp || new Date().toISOString(),
      raw: message
    };

    switch (message.type) {
      case 'user':
        return {
          ...base,
          type: 'user',
          content: message.message?.content || '',
          role: 'user'
        };

      case 'assistant':
        return {
          ...base,
          type: 'assistant',
          content: this.extractAssistantContent(message),
          role: 'assistant',
          toolUse: message.message?.content?.filter(c => c.type === 'tool_use') || []
        };

      case 'tool_result':
        return {
          ...base,
          type: 'tool_result',
          toolId: message.tool_use_id,
          content: message.content
        };

      default:
        return {
          ...base,
          type: message.type || 'unknown',
          content: JSON.stringify(message)
        };
    }
  }

  /**
   * Extract text content from assistant message
   * Handles both string and structured content formats
   *
   * @param {Object} message - Raw assistant message
   * @returns {string} Extracted text content
   */
  extractAssistantContent(message) {
    const content = message.message?.content;

    if (!content) return '';
    if (typeof content === 'string') return content;

    if (Array.isArray(content)) {
      return content
        .filter(c => c.type === 'text')
        .map(c => c.text)
        .join('\n');
    }

    return JSON.stringify(content);
  }

  /**
   * Find active sessions across all projects or specific project
   * Active = modified within last 30 minutes
   *
   * @param {string|null} projectPath - Optional project path filter
   * @returns {Promise<Array>} Array of session objects
   */
  async findActiveSessions(projectPath = null) {
    const sessions = [];
    const projectDirs = projectPath
      ? [path.join(this.claudeProjectsPath, projectPath)]
      : await this.getAllProjectDirs();

    for (const dir of projectDirs) {
      try {
        const files = await fs.readdir(dir);
        const jsonlFiles = files.filter(f => f.endsWith('.jsonl') && !f.startsWith('agent-'));

        for (const file of jsonlFiles) {
          const filePath = path.join(dir, file);
          const stats = await fs.stat(filePath);
          const isRecent = Date.now() - stats.mtimeMs < 30 * 60 * 1000; // 30 minutes

          if (isRecent) {
            const sessionId = file.replace('.jsonl', '');
            const projectName = path.basename(dir);

            sessions.push({
              sessionId,
              projectPath: projectName,
              lastModified: stats.mtime,
              isActive: this.watchers.has(`${projectName}:${sessionId}`)
            });
          }
        }
      } catch (error) {
        // Skip directories that can't be read
        console.error(`[SessionSync] Error reading directory ${dir}:`, error);
      }
    }

    return sessions.sort((a, b) => b.lastModified - a.lastModified);
  }

  /**
   * Get current session for a given working directory
   * Finds most recently modified session in the project
   *
   * @param {string} cwd - Current working directory
   * @returns {Promise<Object|null>} Session object or null
   */
  async getCurrentSession(cwd) {
    try {
      // Claude Code encodes paths as: "/" -> "-", remove leading "/"
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
    } catch (error) {
      console.error('[SessionSync] Error getting current session:', error);
      return null;
    }
  }

  /**
   * Get all project directories in Claude projects folder
   *
   * @returns {Promise<Array<string>>} Array of directory paths
   */
  async getAllProjectDirs() {
    try {
      const entries = await fs.readdir(this.claudeProjectsPath, { withFileTypes: true });
      return entries
        .filter(entry => entry.isDirectory())
        .map(entry => path.join(this.claudeProjectsPath, entry.name));
    } catch (error) {
      console.error('[SessionSync] Error reading projects directory:', error);
      return [];
    }
  }

  /**
   * Clean up all watchers (for shutdown)
   */
  shutdown() {
    console.log('[SessionSync] Shutting down, closing all watchers');

    for (const [watchKey, watchData] of this.watchers.entries()) {
      watchData.watcher.close();
      console.log(`[SessionSync] Closed watcher: ${watchKey}`);
    }

    this.watchers.clear();
  }
}

// Export singleton instance
const sessionSyncService = new SessionSyncService();
export default sessionSyncService;
export { SessionSyncService };
