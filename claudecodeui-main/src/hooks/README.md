# useChatMessages Hook

A production-ready React hook for managing chat messages in the Claude Code UI project. Provides a complete API for handling message state, streaming updates, tool calls, and session-based message persistence.

## Features

- **Message State Management**: Add, update, and clear user/assistant/error messages
- **Streaming Support**: Throttled streaming updates for real-time chat experiences
- **Tool Call Handling**: Track tool executions and their results
- **Pagination**: Load messages incrementally with infinite scroll support
- **Session Persistence**: Load and sync messages from JSONL session files
- **TypeScript-Ready**: Comprehensive JSDoc types for full IntelliSense support
- **Performance Optimized**: Throttled updates, memoization, and efficient state management
- **Callback Hooks**: Optional callbacks for analytics, logging, and side effects

## Installation

The hook is located at `/src/hooks/useChatMessages.js` and can be imported directly:

```javascript
import { useChatMessages } from '../hooks/useChatMessages';
```

## Basic Usage

```javascript
import React, { useEffect } from 'react';
import { useChatMessages } from '../hooks/useChatMessages';

function ChatComponent({ sessionId, projectName }) {
  const {
    messages,
    addUserMessage,
    addAssistantMessage,
    loadMessages,
    isLoading
  } = useChatMessages(sessionId);

  // Load messages when session changes
  useEffect(() => {
    if (sessionId && projectName) {
      loadMessages(projectName, sessionId);
    }
  }, [sessionId, projectName, loadMessages]);

  const handleSendMessage = (text) => {
    addUserMessage(text);
    // Send to backend...
  };

  if (isLoading) {
    return <div>Loading messages...</div>;
  }

  return (
    <div>
      {messages.map((msg) => (
        <div key={msg.id} className={msg.type}>
          {msg.content}
        </div>
      ))}
    </div>
  );
}
```

## API Reference

### Hook Signature

```javascript
const result = useChatMessages(sessionId, options);
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `sessionId` | `string` | Current session ID (optional) |
| `options` | `object` | Configuration options (optional) |
| `options.messagesPerPage` | `number` | Messages per page for pagination (default: 20) |
| `options.onMessageAdded` | `function` | Callback when a message is added |
| `options.onMessagesLoaded` | `function` | Callback when messages are loaded |

#### Return Value

| Property | Type | Description |
|----------|------|-------------|
| `messages` | `Message[]` | Array of all messages |
| `isLoading` | `boolean` | Whether initial messages are loading |
| `isLoadingMore` | `boolean` | Whether more messages are loading |
| `hasMore` | `boolean` | Whether there are more messages to load |
| `totalMessages` | `number` | Total number of messages in session |
| `addUserMessage` | `function` | Add a user message |
| `addAssistantMessage` | `function` | Add an assistant message |
| `updateStreamingMessage` | `function` | Update streaming message content |
| `finalizeStreamingMessage` | `function` | Mark streaming message as complete |
| `addToolCall` | `function` | Add a tool call message |
| `updateToolResult` | `function` | Update tool call with result |
| `addErrorMessage` | `function` | Add an error message |
| `clearMessages` | `function` | Clear all messages |
| `loadMessages` | `function` | Load messages from session |
| `loadMoreMessages` | `function` | Load more messages (pagination) |
| `resetPagination` | `function` | Reset pagination state |
| `setMessages` | `function` | Direct message setter (advanced) |

### Message Object Structure

```typescript
{
  id: string,                      // Unique message ID
  type: 'user' | 'assistant' | 'error',
  content: string | ContentBlock[], // Message content
  timestamp: Date,                  // Message timestamp

  // Optional streaming properties
  isStreaming?: boolean,            // Message is being streamed

  // Optional tool call properties
  isToolUse?: boolean,              // Message represents a tool call
  toolName?: string,                // Tool name
  toolInput?: string,               // Tool input (JSON string)
  toolId?: string,                  // Tool use ID
  toolResult?: {                    // Tool execution result
    content: any,
    isError: boolean,
    timestamp: Date
  },

  // Optional prompt properties
  isInteractivePrompt?: boolean     // Interactive prompt message
}
```

## Usage Examples

### 1. Streaming Messages

Handle real-time streaming responses from WebSocket or SSE:

```javascript
const {
  updateStreamingMessage,
  finalizeStreamingMessage
} = useChatMessages(sessionId);

useEffect(() => {
  if (!websocket) return;

  const handleMessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
      case 'claude-output':
        // Stream chunks (throttled automatically)
        updateStreamingMessage(data.content);
        break;

      case 'claude-complete':
        // Mark streaming as complete
        finalizeStreamingMessage();
        break;
    }
  };

  websocket.addEventListener('message', handleMessage);
  return () => websocket.removeEventListener('message', handleMessage);
}, [websocket]);
```

**Throttling**: By default, streaming updates are throttled to 100ms for performance. You can override this:

```javascript
// Immediate update (no throttling)
updateStreamingMessage('content', { immediate: true });

// Custom throttle delay
updateStreamingMessage('content', { throttleMs: 50 });
```

### 2. Tool Call Handling

Track tool executions and their results:

```javascript
const {
  addToolCall,
  updateToolResult
} = useChatMessages(sessionId);

// When tool is invoked
const toolId = addToolCall(
  'Read',
  { file_path: '/path/to/file.js' },
  'tool_123'
);

// When tool completes
updateToolResult('tool_123', 'File contents here', false);

// When tool fails
updateToolResult('tool_456', 'File not found', true);
```

### 3. Pagination / Infinite Scroll

Load older messages as user scrolls:

```javascript
const {
  messages,
  loadMessages,
  loadMoreMessages,
  hasMore,
  isLoadingMore
} = useChatMessages(sessionId);

const handleScroll = async () => {
  if (isNearTop && hasMore && !isLoadingMore) {
    const olderMessages = await loadMoreMessages(projectName, sessionId);
    // Restore scroll position...
  }
};
```

### 4. Multi-Modal Messages (Text + Images)

Send messages with multiple content blocks:

```javascript
const { addUserMessage } = useChatMessages(sessionId);

// Text + images
addUserMessage([
  { type: 'text', text: 'Analyze these images' },
  { type: 'image', source: { type: 'base64', data: imageData1 } },
  { type: 'image', source: { type: 'base64', data: imageData2 } }
]);
```

### 5. Callbacks for Analytics

Track message events for analytics or logging:

```javascript
const {
  messages,
  addUserMessage
} = useChatMessages(sessionId, {
  onMessageAdded: (message) => {
    // Track in analytics
    analytics.track('Message Added', {
      type: message.type,
      sessionId
    });
  },
  onMessagesLoaded: (messages) => {
    console.log(`Loaded ${messages.length} messages`);
  }
});
```

## Integration with ChatInterface.jsx

The hook is designed to replace the message management logic in `ChatInterface.jsx`. Here's a migration path:

### Before (ChatInterface.jsx)

```javascript
const [chatMessages, setChatMessages] = useState([]);
const [sessionMessages, setSessionMessages] = useState([]);

// Complex message handling logic scattered throughout component...
```

### After (with hook)

```javascript
import { useChatMessages } from '../hooks/useChatMessages';

const {
  messages,
  addUserMessage,
  addAssistantMessage,
  updateStreamingMessage,
  addToolCall,
  updateToolResult,
  loadMessages,
  clearMessages
} = useChatMessages(currentSessionId);

// All message logic is now centralized in the hook
```

## Performance Considerations

### Streaming Optimization

The hook uses throttling to batch rapid streaming updates:

- **Default throttle**: 100ms
- **Buffer management**: Automatic buffering and flushing
- **Memory efficient**: Clears buffers after updates

### Message Rendering

For large message lists, consider virtualization:

```javascript
import { FixedSizeList } from 'react-window';

const MessageList = ({ messages }) => (
  <FixedSizeList
    height={600}
    itemCount={messages.length}
    itemSize={80}
  >
    {({ index, style }) => (
      <div style={style}>
        {messages[index].content}
      </div>
    )}
  </FixedSizeList>
);
```

### Pagination Strategy

Load messages in chunks to avoid loading entire history:

```javascript
const options = {
  messagesPerPage: 20 // Adjust based on average message size
};
```

## Accessibility Checklist

When using this hook in UI components, ensure:

- [ ] Message list has `role="log"` or `role="feed"`
- [ ] New messages are announced to screen readers via `aria-live="polite"`
- [ ] Loading states have appropriate `aria-busy` and `aria-label`
- [ ] Tool calls have descriptive text for assistive technologies
- [ ] Keyboard navigation works for message interactions
- [ ] Focus management is handled when messages are added/updated

Example:

```javascript
<div
  role="log"
  aria-live="polite"
  aria-label="Chat messages"
  aria-busy={isLoading}
>
  {messages.map(msg => (
    <div key={msg.id} role="article" aria-label={`${msg.type} message`}>
      {msg.content}
    </div>
  ))}
</div>
```

## Testing

Comprehensive unit tests are available in `__tests__/useChatMessages.test.js`:

```bash
npm test useChatMessages
```

Test coverage includes:

- Basic message operations (add, clear)
- Streaming updates and throttling
- Tool call handling
- Pagination and loading states
- Error handling
- Callback execution
- Edge cases and race conditions

## Troubleshooting

### Messages not appearing

**Issue**: Messages added but not visible in UI

**Solutions**:
- Check that messages state is being rendered
- Verify `isLoading` state isn't blocking render
- Ensure message IDs are unique

### Streaming messages duplicating

**Issue**: Streaming content appears multiple times

**Solutions**:
- Call `finalizeStreamingMessage()` when stream completes
- Don't mix `updateStreamingMessage` with `addAssistantMessage`
- Check for duplicate WebSocket event listeners

### Pagination not working

**Issue**: `loadMoreMessages` doesn't load anything

**Solutions**:
- Verify `hasMore` is `true`
- Check that `projectName` and `sessionId` are valid
- Ensure backend API supports pagination parameters
- Review console for API errors

### Performance issues with large message lists

**Solutions**:
- Implement message virtualization (react-window)
- Reduce `messagesPerPage` for faster initial loads
- Use `useMemo` for expensive message transformations
- Consider message archiving for very old messages

## Advanced Usage

### Custom Message Filtering

```javascript
const { messages } = useChatMessages(sessionId);

const userMessages = useMemo(
  () => messages.filter(m => m.type === 'user'),
  [messages]
);

const toolCalls = useMemo(
  () => messages.filter(m => m.isToolUse),
  [messages]
);
```

### Message Search

```javascript
const searchMessages = (query) => {
  return messages.filter(msg =>
    typeof msg.content === 'string' &&
    msg.content.toLowerCase().includes(query.toLowerCase())
  );
};
```

### Export Messages

```javascript
const exportMessages = () => {
  const jsonl = messages
    .map(msg => JSON.stringify(msg))
    .join('\n');

  const blob = new Blob([jsonl], { type: 'application/jsonl' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = `session_${sessionId}.jsonl`;
  a.click();
};
```

## Future Enhancements

Potential improvements for future versions:

- [ ] Message editing and deletion
- [ ] Message reactions and annotations
- [ ] Local storage persistence for draft messages
- [ ] Optimistic updates with rollback
- [ ] Message threading/replies
- [ ] Real-time collaboration indicators
- [ ] Message encryption for sensitive data
- [ ] Offline support with sync queue

## Related Files

- `/src/hooks/useChatMessages.js` - Hook implementation
- `/src/hooks/__tests__/useChatMessages.test.js` - Unit tests
- `/src/hooks/useChatMessages.example.jsx` - Usage examples
- `/src/components/ChatInterface.jsx` - Main chat component
- `/src/utils/api.js` - API utilities

## Contributing

When modifying this hook:

1. Update JSDoc type definitions
2. Add corresponding unit tests
3. Update this README with new features
4. Test integration with ChatInterface.jsx
5. Verify performance with large message counts

## License

Part of the Claude Code UI project.
