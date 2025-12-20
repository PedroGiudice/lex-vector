# useChatWebSocket Hook

A production-ready React hook for managing WebSocket connections in the Claude Code UI project.

## Overview

`useChatWebSocket` is a custom React hook that provides robust WebSocket connection management with automatic reconnection, message handling, and proper cleanup. It's specifically designed for real-time communication with the Claude AI backend.

## Features

- **Automatic Connection Management**: Establishes WebSocket connection on mount
- **Auto-Reconnection**: Configurable exponential backoff reconnection strategy
- **Connection State Tracking**: Real-time connection status monitoring
- **Message Buffering**: Queues messages when disconnected, sends on reconnection
- **Type Safety**: Full JSDoc type definitions for better IDE support
- **Error Handling**: Comprehensive error handling and reporting
- **Memory Safe**: Proper cleanup to prevent memory leaks
- **Authentication Support**: Both Platform and OSS mode authentication
- **Multiple Message Types**: Handles all Claude message types (responses, tools, errors, etc.)

## Installation

The hook is located at `/src/hooks/useChatWebSocket.js` and can be imported directly:

```javascript
import { useChatWebSocket } from '@/hooks/useChatWebSocket';
```

## Basic Usage

```javascript
import React, { useState, useCallback } from 'react';
import { useChatWebSocket } from '@/hooks/useChatWebSocket';

function ChatComponent() {
  const [messages, setMessages] = useState([]);

  const handleMessage = useCallback((message) => {
    setMessages(prev => [...prev, message]);
  }, []);

  const {
    isConnected,
    connectionStatus,
    sendMessage,
    lastMessage,
    error
  } = useChatWebSocket({
    url: '/ws',
    onMessage: handleMessage,
    onConnect: () => console.log('Connected!'),
    onDisconnect: () => console.log('Disconnected!'),
    autoReconnect: true
  });

  const handleSend = () => {
    sendMessage({
      type: 'user-message',
      content: 'Hello, Claude!'
    });
  };

  return (
    <div>
      <div>Status: {connectionStatus}</div>
      <button onClick={handleSend} disabled={!isConnected}>
        Send Message
      </button>
    </div>
  );
}
```

## API Reference

### Parameters

The hook accepts a configuration object with the following options:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `string` | **required** | WebSocket server URL (e.g., '/ws' or 'ws://localhost:3000/ws') |
| `onMessage` | `function` | `undefined` | Callback fired when a message is received |
| `onConnect` | `function` | `undefined` | Callback fired when connection opens |
| `onDisconnect` | `function` | `undefined` | Callback fired when connection closes |
| `onError` | `function` | `undefined` | Callback fired on errors |
| `autoReconnect` | `boolean` | `true` | Whether to automatically reconnect on disconnect |
| `reconnectDelay` | `number` | `3000` | Initial delay (ms) before reconnection attempt |
| `maxReconnectAttempts` | `number` | `Infinity` | Maximum number of reconnection attempts |
| `token` | `string` | `null` | Authentication token (for OSS mode) |
| `isPlatform` | `boolean` | `false` | Whether running in platform mode |

### Return Value

The hook returns an object with the following properties:

| Property | Type | Description |
|----------|------|-------------|
| `isConnected` | `boolean` | Whether WebSocket is currently connected |
| `connectionStatus` | `string` | Current status: 'connecting', 'connected', 'disconnected', or 'error' |
| `sendMessage` | `function` | Function to send messages (auto-buffers if disconnected) |
| `lastMessage` | `object` | Most recent message received |
| `error` | `Event` | Most recent error (if any) |
| `reconnect` | `function` | Manually trigger reconnection |
| `disconnect` | `function` | Manually disconnect |
| `reconnectAttempts` | `number` | Number of reconnection attempts made |

## Message Types

The hook handles the following WebSocket message types:

### Claude Messages
- `session-created`: New session started
- `claude-response`: Claude response chunk
- `claude-output`: Raw output from Claude
- `claude-complete`: Response complete
- `claude-error`: Error occurred
- `claude-interactive-prompt`: Interactive prompt from CLI

### Cursor Messages
- `cursor-system`: System/init messages
- `cursor-user`: User messages (echoes)
- `cursor-tool-use`: Tool usage
- `cursor-output`: Raw terminal output
- `cursor-result`: Completion result
- `cursor-error`: Error occurred

### Tool Messages
- `tool-use`: Tool call started
- `tool-result`: Tool call result

### System Messages
- `session-aborted`: Session cancelled
- `projects_updated`: Project list updated
- `taskmaster-project-updated`: Task master project updated
- `token-budget`: Token usage update

## Advanced Usage

### Custom Reconnection Strategy

```javascript
const { isConnected, reconnectAttempts } = useChatWebSocket({
  url: '/ws',
  autoReconnect: true,
  reconnectDelay: 2000,      // Start with 2 seconds
  maxReconnectAttempts: 5,   // Try 5 times max
  onDisconnect: () => {
    console.log('Disconnected, will retry...');
  }
});
```

The hook implements exponential backoff with a multiplier of 1.5 and a maximum delay of 30 seconds.

### Message Buffering

Messages sent while disconnected are automatically buffered and sent when the connection is re-established:

```javascript
const { sendMessage, isConnected } = useChatWebSocket({ url: '/ws' });

// This will be buffered if not connected
sendMessage({ type: 'user-message', content: 'Hello' });
```

### Session-Based Filtering

Filter messages by session ID to prevent cross-session interference:

```javascript
const handleMessage = useCallback((message) => {
  // Global messages apply to all sessions
  const globalTypes = ['projects_updated', 'session-created'];
  const isGlobal = globalTypes.includes(message.type);

  // Filter by session ID
  if (!isGlobal && message.sessionId && message.sessionId !== currentSessionId) {
    return; // Ignore messages for other sessions
  }

  // Process message
  processMessage(message);
}, [currentSessionId]);

const { sendMessage } = useChatWebSocket({
  url: '/ws',
  onMessage: handleMessage
});
```

### Authentication (OSS Mode)

```javascript
const token = localStorage.getItem('auth-token');

const { isConnected } = useChatWebSocket({
  url: '/ws',
  token,
  isPlatform: false  // OSS mode
});
```

### Manual Connection Control

```javascript
const {
  isConnected,
  reconnect,
  disconnect
} = useChatWebSocket({
  url: '/ws',
  autoReconnect: false  // Disable auto-reconnect
});

// Manually control connection
const handleReconnect = () => reconnect();
const handleDisconnect = () => disconnect();
```

## Error Handling

The hook provides multiple ways to handle errors:

```javascript
const {
  error,
  connectionStatus,
  reconnectAttempts
} = useChatWebSocket({
  url: '/ws',
  onError: (err) => {
    console.error('WebSocket error:', err);
    // Show user notification
  },
  maxReconnectAttempts: 3
});

// Check for error state
if (connectionStatus === 'error') {
  if (reconnectAttempts >= 3) {
    // Max retries reached
    return <div>Failed to connect. Please refresh the page.</div>;
  }
}
```

## Performance Considerations

### Message Buffering
- Messages are buffered in memory when disconnected
- No size limit on buffer (consider implementing if needed)
- Buffered messages are sent in order when reconnected

### Reconnection Backoff
- Initial delay: 3 seconds (configurable)
- Exponential backoff with 1.5x multiplier
- Maximum delay capped at 30 seconds
- Prevents server overload during outages

### Memory Management
- Automatic cleanup on unmount
- Clears timeouts and closes connections
- No memory leaks from stale closures

## Testing

Comprehensive test suite included in `useChatWebSocket.test.js`:

```bash
npm test useChatWebSocket.test.js
```

Test coverage includes:
- Connection management
- Message handling
- Reconnection logic
- Error handling
- Cleanup on unmount
- Message buffering
- Authentication modes

## Examples

See `useChatWebSocket.example.jsx` for complete working examples:

1. **Basic Chat Example**: Simple message sending/receiving
2. **Advanced Chat**: Handling multiple message types
3. **Custom Reconnection**: Exponential backoff demonstration
4. **Authenticated Chat**: Token-based authentication
5. **Refactored ChatInterface**: Integration pattern for existing code

## Migration Guide

### From Existing ChatInterface.jsx

The current `ChatInterface.jsx` receives WebSocket as a prop. To refactor:

**Before:**
```javascript
function ChatInterface({ ws, sendMessage, messages }) {
  // Uses props passed from parent
}
```

**After:**
```javascript
function ChatInterface() {
  const {
    isConnected,
    sendMessage,
    lastMessage
  } = useChatWebSocket({
    url: '/ws',
    onMessage: handleWebSocketMessage
  });

  // Direct WebSocket control within component
}
```

### From utils/websocket.js

The existing `useWebSocket` in `utils/websocket.js` can be replaced:

**Before:**
```javascript
import { useWebSocket } from '../utils/websocket';

function App() {
  const { ws, sendMessage, messages, isConnected } = useWebSocket();
}
```

**After:**
```javascript
import { useChatWebSocket } from '@/hooks/useChatWebSocket';

function App() {
  const {
    isConnected,
    sendMessage,
    lastMessage
  } = useChatWebSocket({
    url: '/ws',
    onMessage: handleMessage
  });
}
```

## Browser Compatibility

- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+

Requires WebSocket API support (all modern browsers).

## Troubleshooting

### Connection Keeps Failing

```javascript
// Check connection status and error details
const { connectionStatus, error, reconnectAttempts } = useChatWebSocket({
  url: '/ws',
  onError: (err) => console.error('Connection error:', err)
});

console.log('Status:', connectionStatus);
console.log('Error:', error);
console.log('Attempts:', reconnectAttempts);
```

### Messages Not Being Received

```javascript
// Verify onMessage callback is being called
const { lastMessage } = useChatWebSocket({
  url: '/ws',
  onMessage: (msg) => {
    console.log('Received:', msg);  // Debug log
  }
});

// Check lastMessage state
console.log('Last message:', lastMessage);
```

### Authentication Issues (OSS Mode)

```javascript
// Ensure token is present
const token = localStorage.getItem('auth-token');
if (!token) {
  console.error('No auth token found');
}

const { isConnected } = useChatWebSocket({
  url: '/ws',
  token,
  isPlatform: false
});
```

## Performance Tips

1. **Memoize Callbacks**: Use `useCallback` for event handlers to prevent unnecessary reconnections
2. **Debounce Send**: For rapid messages, consider debouncing
3. **Message Processing**: Handle heavy processing in `useEffect` with dependencies
4. **Cleanup**: Always allow the hook to cleanup (don't override)

## Related Files

- `/src/hooks/useChatWebSocket.js` - Main hook implementation
- `/src/hooks/useChatWebSocket.test.js` - Test suite
- `/src/hooks/useChatWebSocket.example.jsx` - Usage examples
- `/src/utils/websocket.js` - Original WebSocket utility (can be replaced)
- `/src/contexts/WebSocketContext.jsx` - Context provider (uses original utility)
- `/src/components/ChatInterface.jsx` - Main chat component (uses WebSocket)

## Future Enhancements

Potential improvements for future versions:

- [ ] Message queue size limit with overflow handling
- [ ] Ping/pong heartbeat for connection health monitoring
- [ ] Connection quality metrics (latency, packet loss)
- [ ] TypeScript migration for better type safety
- [ ] Retry queue for failed messages
- [ ] Message acknowledgment system
- [ ] Compression support for large messages
- [ ] Multiple simultaneous WebSocket connections

## License

Part of the Claude Code UI project.

## Support

For issues or questions:
1. Check the examples in `useChatWebSocket.example.jsx`
2. Review test cases in `useChatWebSocket.test.js`
3. Check the troubleshooting section above
4. Review the existing ChatInterface.jsx implementation

---

**Created**: December 2024
**Version**: 1.0.0
**Author**: Claude Code Refactoring Project
