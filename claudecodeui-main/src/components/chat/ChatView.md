# ChatView Component

## Overview

`ChatView` is a container component that orchestrates the modular chat interface. It replaces the monolithic `ChatInterface.jsx` (4788 lines) with a clean, maintainable architecture using smaller, focused components.

## Architecture

### Component Hierarchy

```
ChatView (Container)
├── ChatHeader (Model selection, project name)
├── MessageList (Conversation display)
│   ├── MessageBubble (Individual messages)
│   └── EmptyState
├── ThinkingIndicator (AI processing state)
└── ChatInput (Message input)
```

### Responsibilities

- **State Management**: Manages chat messages, processing state, and WebSocket communication
- **Session Handling**: Tracks session lifecycle (creation, activation, completion)
- **Message Persistence**: Saves/loads messages and preferences to/from localStorage
- **WebSocket Integration**: Handles real-time message exchange
- **Component Orchestration**: Coordinates child components and manages data flow

## Props API

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `selectedProject` | Object | Yes | Currently selected project |
| `selectedSession` | Object | No | Currently selected chat session |
| `ws` | WebSocket | No | WebSocket connection for real-time communication |
| `sendMessage` | Function | No | Custom function to send messages (overrides WebSocket) |
| `messages` | Array | No | Initial messages array |
| `onFileOpen` | Function | No | Callback when a file is clicked in messages |
| `onInputFocusChange` | Function | No | Callback for input focus changes |
| `onSessionActive` | Function | No | Callback when session becomes active |
| `onSessionInactive` | Function | No | Callback when session becomes inactive |
| `onSessionProcessing` | Function | No | Callback when processing starts |
| `onSessionNotProcessing` | Function | No | Callback when processing stops |
| `processingSessions` | Set | No | Set of currently processing session IDs |
| `onReplaceTemporarySession` | Function | No | Callback to replace temporary session with real one |
| `onNavigateToSession` | Function | No | Callback to navigate to a session |
| `onShowSettings` | Function | No | Callback to show settings panel |
| `autoExpandTools` | Boolean | No | Whether to auto-expand tool calls (default: false) |
| `showRawParameters` | Boolean | No | Whether to show raw parameters (default: false) |
| `showThinking` | Boolean | No | Whether to show thinking indicator (default: true) |
| `autoScrollToBottom` | Boolean | No | Whether to auto-scroll to bottom (default: true) |
| `sendByCtrlEnter` | Boolean | No | Whether to send by Ctrl+Enter (default: false) |
| `externalMessageUpdate` | Number | No | External trigger for message updates |
| `onShowAllTasks` | Function | No | Callback to show all tasks |

## Usage Examples

### Basic Usage

```jsx
import ChatView from './components/chat/ChatView';

function App() {
  const [project, setProject] = useState(null);
  const [ws, setWs] = useState(null);

  return (
    <ChatView
      selectedProject={project}
      ws={ws}
    />
  );
}
```

### With Session Management

```jsx
import ChatView from './components/chat/ChatView';

function ChatContainer() {
  const [project, setProject] = useState({ id: '1', name: 'My Project' });
  const [session, setSession] = useState({ id: 'session-1' });
  const [ws, setWs] = useState(null);

  const handleSessionActive = (sessionId) => {
    console.log('Session active:', sessionId);
    // Pause sidebar updates, lock UI, etc.
  };

  const handleSessionInactive = (sessionId) => {
    console.log('Session inactive:', sessionId);
    // Resume sidebar updates, unlock UI, etc.
  };

  return (
    <ChatView
      selectedProject={project}
      selectedSession={session}
      ws={ws}
      onSessionActive={handleSessionActive}
      onSessionInactive={handleSessionInactive}
    />
  );
}
```

### With Custom Message Sender

```jsx
import ChatView from './components/chat/ChatView';

function CustomChatView() {
  const [project, setProject] = useState({ id: '1', name: 'My Project' });

  const customSendMessage = async (messageData) => {
    // Custom API call instead of WebSocket
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(messageData)
    });

    const result = await response.json();
    // Handle response...
  };

  return (
    <ChatView
      selectedProject={project}
      sendMessage={customSendMessage}
    />
  );
}
```

### With File Opening

```jsx
import ChatView from './components/chat/ChatView';

function ChatWithFiles() {
  const [project, setProject] = useState({ id: '1', name: 'My Project' });

  const handleFileOpen = (filePath) => {
    console.log('Opening file:', filePath);
    // Open file in editor, preview panel, etc.
  };

  return (
    <ChatView
      selectedProject={project}
      onFileOpen={handleFileOpen}
    />
  );
}
```

### Full Integration Example

```jsx
import { useState, useEffect, useRef } from 'react';
import ChatView from './components/chat/ChatView';

function FullChatExample() {
  const [project, setProject] = useState({
    id: '1',
    name: 'My Project',
    path: '/path/to/project'
  });
  const [session, setSession] = useState(null);
  const [ws, setWs] = useState(null);
  const [processingSessions, setProcessingSessions] = useState(new Set());

  // Initialize WebSocket
  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:3000');

    websocket.onopen = () => {
      console.log('WebSocket connected');
      setWs(websocket);
    };

    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      setWs(null);
    };

    return () => {
      websocket.close();
    };
  }, []);

  const handleSessionActive = (sessionId) => {
    console.log('Session active:', sessionId);
    setProcessingSessions(prev => new Set(prev).add(sessionId));
  };

  const handleSessionInactive = (sessionId) => {
    console.log('Session inactive:', sessionId);
    setProcessingSessions(prev => {
      const newSet = new Set(prev);
      newSet.delete(sessionId);
      return newSet;
    });
  };

  const handleReplaceTemporarySession = (tempId, realId) => {
    console.log('Replace temp session:', tempId, 'with:', realId);
    if (session?.id === tempId) {
      setSession({ ...session, id: realId });
    }
  };

  const handleFileOpen = (filePath) => {
    console.log('Open file:', filePath);
    // Implement file opening logic
  };

  return (
    <div className="h-screen">
      <ChatView
        selectedProject={project}
        selectedSession={session}
        ws={ws}
        onSessionActive={handleSessionActive}
        onSessionInactive={handleSessionInactive}
        onReplaceTemporarySession={handleReplaceTemporarySession}
        onFileOpen={handleFileOpen}
        processingSessions={processingSessions}
        autoScrollToBottom={true}
        showThinking={true}
      />
    </div>
  );
}
```

## WebSocket Message Protocol

### Outgoing Messages (Client → Server)

```javascript
// Send chat message
{
  type: 'chat-message',
  content: 'User message content',
  sessionId: 'session-id',
  projectId: 'project-id',
  projectName: 'Project Name',
  model: 'claude-sonnet-4-20250514'
}
```

### Incoming Messages (Server → Client)

```javascript
// Session created
{
  type: 'session-created',
  sessionId: 'new-session-id',
  temporaryId: 'temp-id' // optional
}

// New message
{
  type: 'message',
  role: 'assistant',
  content: 'Message content',
  messageId: 'unique-id',
  timestamp: 1234567890,
  toolCalls: [], // optional
  toolResults: [] // optional
}

// Thinking started
{
  type: 'thinking'
}

// Thinking complete
{
  type: 'thinking-complete'
}

// Processing started
{
  type: 'processing-start'
}

// Processing complete
{
  type: 'processing-complete'
}

// Conversation complete
{
  type: 'claude-complete'
}

// Session aborted
{
  type: 'session-aborted'
}

// Error
{
  type: 'error',
  message: 'Error message'
}
```

## State Management

### Internal State

- `chatMessages`: Array of message objects
- `currentModel`: Selected AI model ID
- `isProcessing`: Boolean indicating if AI is processing
- `isThinking`: Boolean indicating if AI is thinking
- `currentSessionId`: Current session identifier
- `input`: Current input value (internal to ChatInput)

### Message Object Structure

```javascript
{
  id: 'unique-id', // Unique message identifier
  role: 'user' | 'assistant', // Message role
  type: 'user' | 'assistant' | 'error', // Message type
  content: 'Message content', // Text content
  timestamp: Date, // Message timestamp
  toolCalls: [], // Optional: Tool calls made
  toolResults: [] // Optional: Tool results
}
```

## LocalStorage Persistence

The component automatically persists the following to localStorage:

- **Model Selection**: `chat_model_{projectName}`
  - Stores the selected model per project

- **Chat Messages**: `chat_messages_{projectName}`
  - Stores conversation history per project
  - Automatically loaded when project is selected
  - Saved after each message update

## Performance Considerations

### Optimizations Implemented

1. **useCallback Hooks**: All event handlers use `useCallback` to prevent unnecessary re-renders
2. **Message Deduplication**: Prevents duplicate messages with the same ID
3. **Ref Updates**: WebSocket and session ID stored in refs to avoid re-creating listeners
4. **Conditional Rendering**: Thinking indicator only renders when needed
5. **Local Storage Throttling**: Messages saved only when they change

### Performance Tips

- Use `autoScrollToBottom={false}` for large message histories to reduce scroll calculations
- Consider implementing message pagination for conversations with 100+ messages
- Use `showThinking={false}` if you have custom loading indicators

## Accessibility

### Keyboard Navigation

- Input field is keyboard accessible
- Send button can be triggered with Enter (or Ctrl+Enter if configured)
- Focus management handled by child components

### Screen Reader Support

- Semantic HTML structure
- ARIA labels on interactive elements (via child components)
- Message role announcements (user vs assistant)

### Color Contrast

- All text meets WCAG 2.1 AA standards
- Zinc color palette provides excellent contrast ratios
- Orange accents used sparingly for emphasis

## Testing

### Running Tests

```bash
npm test -- ChatView.test.jsx
```

### Test Coverage

- Component rendering
- Message sending (WebSocket and custom sender)
- Session lifecycle management
- WebSocket message handling
- State persistence
- Error handling
- Message deduplication

### Example Test

```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import ChatView from './ChatView';

test('sends message when send button clicked', async () => {
  const mockSendMessage = jest.fn();
  const project = { id: '1', name: 'Test' };

  render(
    <ChatView
      selectedProject={project}
      sendMessage={mockSendMessage}
    />
  );

  // Simulate sending a message
  // (exact implementation depends on ChatInput mock)

  expect(mockSendMessage).toHaveBeenCalled();
});
```

## Migration from ChatInterface.jsx

### Key Differences

1. **Modular Structure**: Functionality split across focused components
2. **Simplified Props**: Cleaner prop interface with better documentation
3. **WebSocket Handling**: Centralized in ChatView instead of scattered
4. **State Management**: Clearer state ownership and updates
5. **Size**: ~350 lines vs 4788 lines (92.7% reduction)

### Migration Steps

1. Replace `<ChatInterface />` with `<ChatView />`
2. Update prop names if necessary (most are compatible)
3. Test WebSocket integration
4. Verify session management callbacks
5. Check localStorage persistence

### Breaking Changes

- Image upload handling simplified (may need adjustment)
- Custom command execution moved to separate handler
- Markdown rendering delegated to MessageContent component
- Voice input moved to separate component

## Troubleshooting

### Messages not appearing

- Check that `selectedProject` is set
- Verify WebSocket connection is open
- Check browser console for errors
- Verify message structure matches protocol

### Session not updating

- Ensure `onReplaceTemporarySession` is implemented
- Check that session IDs are being passed correctly
- Verify WebSocket `session-created` event is received

### LocalStorage not persisting

- Check browser storage quota
- Verify project name is consistent
- Check for localStorage errors in console
- Try clearing localStorage and reloading

### WebSocket disconnecting

- Check WebSocket server is running
- Verify WebSocket URL is correct
- Check for network issues
- Implement reconnection logic in parent component

## Best Practices

1. **Always provide `selectedProject`** - Required for proper functionality
2. **Implement session callbacks** - Enables proper UI state management
3. **Handle WebSocket lifecycle** - Connect, disconnect, reconnect in parent
4. **Use custom sendMessage for complex scenarios** - Easier to test and debug
5. **Monitor localStorage usage** - Large conversations can fill storage
6. **Implement error boundaries** - Catch and handle component errors gracefully

## Future Enhancements

Planned improvements:

- [ ] Message pagination for large conversations
- [ ] Image attachment support
- [ ] Voice input integration
- [ ] Message search functionality
- [ ] Export conversation feature
- [ ] Keyboard shortcuts
- [ ] Custom theme support
- [ ] Real-time typing indicators
- [ ] Message reactions
- [ ] Thread support
