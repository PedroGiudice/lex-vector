/**
 * WebSocket Route for Session Sync
 */
import sessionSyncService from '../services/sessionSync.js';

export function handleSessionSyncConnection(ws, req) {
  let currentSubscription = null;

  ws.on('message', async (message) => {
    try {
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
          } else {
            ws.send(JSON.stringify({ type: 'error', error: 'No active session found' }));
          }
          break;

        case 'list_sessions':
          const sessions = await sessionSyncService.findActiveSessions(data.projectPath);
          ws.send(JSON.stringify({ type: 'sessions_list', sessions }));
          break;

        case 'unsubscribe':
          if (currentSubscription) {
            sessionSyncService.unsubscribe(currentSubscription.projectPath, currentSubscription.sessionId, ws);
            currentSubscription = null;
            ws.send(JSON.stringify({ type: 'unsubscribed' }));
          }
          break;
      }
    } catch (err) {
      ws.send(JSON.stringify({ type: 'error', error: err.message }));
    }
  });

  ws.on('close', () => {
    if (currentSubscription) {
      sessionSyncService.unsubscribe(currentSubscription.projectPath, currentSubscription.sessionId, ws);
    }
  });

  ws.send(JSON.stringify({ type: 'connected' }));
}
