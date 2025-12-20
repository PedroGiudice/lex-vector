# useChatMessages Hook - Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Claude Code UI                               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       ChatInterface.jsx                              │
│                          (Main Component)                            │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  useChatMessages Hook                                        │   │
│  │                                                               │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │   │
│  │  │   State     │  │   Actions    │  │   Session Mgmt   │   │   │
│  │  ├─────────────┤  ├──────────────┤  ├──────────────────┤   │   │
│  │  │ messages    │  │ addUser      │  │ loadMessages     │   │   │
│  │  │ isLoading   │  │ addAssistant │  │ loadMore         │   │   │
│  │  │ hasMore     │  │ addToolCall  │  │ resetPagination  │   │   │
│  │  │ total       │  │ updateStream │  └──────────────────┘   │   │
│  │  └─────────────┘  └──────────────┘                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                  │                                   │
└──────────────────────────────────┼───────────────────────────────────┘
                                  │
                   ┌──────────────┴──────────────┐
                   ▼                             ▼
        ┌─────────────────────┐      ┌─────────────────────┐
        │   WebSocket API     │      │   HTTP API          │
        │   (Real-time)       │      │   (Session Load)    │
        ├─────────────────────┤      ├─────────────────────┤
        │ • Stream chunks     │      │ • GET /sessions     │
        │ • Tool calls        │      │ • JSONL parsing     │
        │ • Tool results      │      │ • Pagination        │
        │ • Completions       │      └─────────────────────┘
        └─────────────────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │   Backend Server    │
        │   (Node.js/Python)  │
        └─────────────────────┘
```

## Component Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                          User Interaction                             │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        ChatInterface.jsx                              │
│                                                                       │
│  handleSubmit(text) ─────────────┐                                   │
│                                   ▼                                   │
│                       addUserMessage(text) ──────────┐               │
│                                                       │               │
│                                   ┌───────────────────┘               │
│                                   ▼                                   │
│                         [Update messages state]                      │
│                                   │                                   │
│                                   ▼                                   │
│                          Re-render with new message                  │
└───────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                          Send via WebSocket
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     WebSocket Message Handler                         │
│                                                                       │
│  ws.onmessage(event) ────────────┐                                   │
│                                   ▼                                   │
│                         Parse message type                           │
│                                   │                                   │
│                  ┌────────────────┼────────────────┐                 │
│                  ▼                ▼                ▼                 │
│          'claude-output'   'tool-use'      'claude-complete'         │
│                  │                │                │                 │
│                  ▼                ▼                ▼                 │
│        updateStreamingMessage  addToolCall  finalizeStreamingMessage │
│                  │                │                │                 │
│                  └────────────────┼────────────────┘                 │
│                                   ▼                                   │
│                         [Update messages state]                      │
│                                   │                                   │
│                                   ▼                                   │
│                          Re-render with updates                      │
└───────────────────────────────────────────────────────────────────────┘
```

## Hook Internal Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      useChatMessages Hook                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                        State Layer                            │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ useState                                                       │  │
│  │ • messages: Message[]                                         │  │
│  │ • isLoading: boolean                                          │  │
│  │ • isLoadingMore: boolean                                      │  │
│  │ • messagesOffset: number                                      │  │
│  │ • hasMore: boolean                                            │  │
│  │ • totalMessages: number                                       │  │
│  │                                                                 │  │
│  │ useRef                                                         │  │
│  │ • streamBufferRef: string (accumulates chunks)                │  │
│  │ • streamTimerRef: TimeoutID (throttling)                      │  │
│  │ • messageIdCounterRef: number (unique IDs)                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Action Layer                               │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ useCallback (memoized functions)                              │  │
│  │                                                                 │  │
│  │ Message Operations:                                           │  │
│  │ • addUserMessage(content, metadata) → messageId               │  │
│  │ • addAssistantMessage(content, metadata) → messageId          │  │
│  │ • addErrorMessage(error) → messageId                          │  │
│  │ • clearMessages() → void                                      │  │
│  │                                                                 │  │
│  │ Streaming Operations:                                         │  │
│  │ • updateStreamingMessage(chunk, options) → void               │  │
│  │   ├─ Buffer chunk in streamBufferRef                          │  │
│  │   ├─ Set throttle timer (100ms default)                       │  │
│  │   └─ Flush buffer on timer expiry                             │  │
│  │ • finalizeStreamingMessage() → void                           │  │
│  │   ├─ Clear any pending timers                                 │  │
│  │   ├─ Flush remaining buffer                                   │  │
│  │   └─ Remove isStreaming flag                                  │  │
│  │                                                                 │  │
│  │ Tool Call Operations:                                         │  │
│  │ • addToolCall(name, input, toolId) → messageId                │  │
│  │ • updateToolResult(toolId, result, isError) → void            │  │
│  │                                                                 │  │
│  │ Session Operations:                                           │  │
│  │ • loadMessages(projectName, sessionId) → Promise<Message[]>   │  │
│  │   ├─ Call api.sessionMessages()                               │  │
│  │   ├─ Convert raw messages to UI format                        │  │
│  │   ├─ Update pagination state                                  │  │
│  │   └─ Return converted messages                                │  │
│  │ • loadMoreMessages(projectName, sessionId) → Promise<...>     │  │
│  │   ├─ Check hasMore flag                                       │  │
│  │   ├─ Load with current offset                                 │  │
│  │   ├─ Prepend to existing messages                             │  │
│  │   └─ Update offset and hasMore                                │  │
│  │ • resetPagination() → void                                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Helper Layer                               │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ • generateMessageId() → string                                │  │
│  │   └─ `msg_${timestamp}_${counter++}`                          │  │
│  │                                                                 │  │
│  │ • convertRawMessages(rawMessages) → Message[]                 │  │
│  │   ├─ Handle string messages                                   │  │
│  │   ├─ Handle structured messages                               │  │
│  │   └─ Add IDs and timestamps                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Lifecycle Layer                              │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ useMemo                                                        │  │
│  │ • Cleanup function (clears timers on unmount)                 │  │
│  │                                                                 │  │
│  │ Callbacks (optional)                                          │  │
│  │ • onMessageAdded(message)                                     │  │
│  │ • onMessagesLoaded(messages)                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## State Transitions

### Message Addition Flow

```
┌─────────────────────┐
│  addUserMessage()   │
│  addAssistantMessage│
│  addToolCall()      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────┐
│ generateMessageId()      │
│ (msg_timestamp_counter)  │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Create message object   │
│ {id, type, content,     │
│  timestamp, ...}        │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ setMessages(prev =>     │
│   [...prev, newMsg])    │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Call onMessageAdded     │
│ callback (if provided)  │
└─────────────────────────┘
           │
           ▼
┌─────────────────────────┐
│ Return messageId        │
└─────────────────────────┘
```

### Streaming Flow

```
┌────────────────────────────┐
│ updateStreamingMessage()   │
│ (called multiple times)    │
└─────────────┬──────────────┘
              │
              ▼
       ┌──────────────┐
       │ chunk empty? │
       └──────┬───────┘
              │ No
              ▼
     ┌────────────────────┐
     │ immediate=true?    │
     └─────┬──────────────┘
           │
    ┌──────┴──────┐
    │ Yes         │ No
    ▼             ▼
┌───────────┐  ┌─────────────────────┐
│ Update    │  │ Add to buffer       │
│ directly  │  │ streamBufferRef +=  │
└───────────┘  │ chunk               │
               └──────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Timer exists?      │
                └─────┬──────────────┘
                      │ No
                      ▼
          ┌───────────────────────────┐
          │ Create throttle timer     │
          │ (100ms default)           │
          └──────────┬────────────────┘
                     │
          ┌──────────▼────────────┐
          │  Timer expires        │
          └──────────┬────────────┘
                     │
                     ▼
          ┌─────────────────────────┐
          │ Flush buffer to message │
          │ Clear buffer & timer    │
          └─────────────────────────┘
                     │
                     ▼
          ┌─────────────────────────┐
          │ Re-render with update   │
          └─────────────────────────┘
```

### Session Loading Flow

```
┌────────────────────────┐
│ loadMessages()         │
│ (projectName, sessId)  │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ setIsLoading(true)     │
└──────────┬─────────────┘
           │
           ▼
┌─────────────────────────────┐
│ api.sessionMessages()       │
│ (messagesPerPage, offset=0) │
└──────────┬──────────────────┘
           │
           ▼
     ┌─────────────┐
     │ Success?    │
     └──────┬──────┘
            │
    ┌───────┴────────┐
    │ Yes            │ No
    ▼                ▼
┌────────────┐  ┌───────────────┐
│ Parse data │  │ addErrorMsg() │
└─────┬──────┘  └───────────────┘
      │
      ▼
┌──────────────────────┐
│ convertRawMessages() │
│ (format for UI)      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ setMessages()        │
│ setHasMore()         │
│ setTotalMessages()   │
│ setMessagesOffset()  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ onMessagesLoaded()   │
│ callback             │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ setIsLoading(false)  │
└──────────────────────┘
```

## Integration Points

### 1. ChatInterface.jsx

**Current responsibilities:**
- Render messages
- Handle user input
- Manage WebSocket connection
- Handle session switching

**After integration:**
- Render messages from hook
- Call hook methods for operations
- WebSocket handlers use hook methods
- Simpler state management

### 2. WebSocket Integration

```javascript
// In ChatInterface.jsx
const {
  updateStreamingMessage,
  finalizeStreamingMessage,
  addToolCall,
  updateToolResult
} = useChatMessages(sessionId);

useEffect(() => {
  if (!ws) return;

  const handleMessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
      case 'claude-output':
        updateStreamingMessage(data.content);
        break;

      case 'tool-use':
        addToolCall(data.name, data.input, data.id);
        break;

      case 'tool-result':
        updateToolResult(data.toolId, data.result, data.isError);
        break;

      case 'claude-complete':
        finalizeStreamingMessage();
        break;
    }
  };

  ws.addEventListener('message', handleMessage);
  return () => ws.removeEventListener('message', handleMessage);
}, [ws]);
```

### 3. Session Management

```javascript
// Load messages when session changes
useEffect(() => {
  if (selectedSession && selectedProject) {
    loadMessages(selectedProject.name, selectedSession.id);
  }
}, [selectedSession, selectedProject, loadMessages]);

// Load more on scroll
const handleScroll = async () => {
  if (isNearTop && hasMore && !isLoadingMore) {
    await loadMoreMessages(projectName, sessionId);
  }
};
```

## Performance Characteristics

### Memory Usage

```
Base hook overhead:     ~1KB
Per message:            ~500 bytes (avg)
1000 messages:          ~500KB
Stream buffer:          <10KB (max)
Total (1000 messages):  ~511KB ✅
```

### Operation Complexity

| Operation | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| Add message | O(1) | O(1) |
| Update streaming | O(1) | O(1) |
| Add tool call | O(1) | O(1) |
| Update tool result | O(n) | O(1) |
| Load messages | O(n) | O(n) |
| Clear messages | O(1) | O(1) |

### Render Optimization

- **Memoized callbacks**: Prevent re-creation on every render
- **Throttled streaming**: Batch updates (100ms)
- **Efficient state updates**: Use functional setState
- **Cleanup on unmount**: Clear timers and buffers

## Error Handling Strategy

```
┌───────────────────────┐
│  Operation Called     │
└──────────┬────────────┘
           │
           ▼
     ┌─────────────┐
     │ Try/Catch   │
     └──────┬──────┘
            │
    ┌───────┴────────┐
    │ Success        │ Error
    ▼                ▼
┌──────────┐   ┌──────────────┐
│ Execute  │   │ Log error    │
│ normally │   │ to console   │
└──────────┘   └──────┬───────┘
                      │
                      ▼
               ┌──────────────┐
               │ Add error    │
               │ message to   │
               │ chat         │
               └──────┬───────┘
                      │
                      ▼
               ┌──────────────┐
               │ Return safe  │
               │ fallback     │
               │ ([], null)   │
               └──────────────┘
```

## Testing Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   Test Suite                                  │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Unit Tests (28 test cases)                                  │
│  ├─ Basic Operations                                         │
│  │  ├─ Initialize with empty state                           │
│  │  ├─ Add user message                                      │
│  │  ├─ Add assistant message                                 │
│  │  ├─ Add error message                                     │
│  │  └─ Clear messages                                        │
│  │                                                             │
│  ├─ Streaming                                                │
│  │  ├─ Throttled updates                                     │
│  │  ├─ Immediate updates                                     │
│  │  ├─ Finalize streaming                                    │
│  │  ├─ Flush buffer on finalize                              │
│  │  └─ Ignore empty chunks                                   │
│  │                                                             │
│  ├─ Tool Calls                                               │
│  │  ├─ Add tool call                                         │
│  │  ├─ Update tool result (success)                          │
│  │  ├─ Update tool result (error)                            │
│  │  └─ Update correct tool only                              │
│  │                                                             │
│  ├─ Session Loading                                          │
│  │  ├─ Load messages successfully                            │
│  │  ├─ Handle load errors                                    │
│  │  ├─ Set loading state                                     │
│  │  └─ Validate parameters                                   │
│  │                                                             │
│  ├─ Pagination                                               │
│  │  ├─ Load more messages                                    │
│  │  ├─ Respect hasMore flag                                  │
│  │  ├─ Update offset correctly                               │
│  │  └─ Prepend older messages                                │
│  │                                                             │
│  ├─ Callbacks                                                │
│  │  ├─ Call onMessageAdded                                   │
│  │  └─ Call onMessagesLoaded                                 │
│  │                                                             │
│  └─ Edge Cases                                               │
│     ├─ Unique message IDs                                    │
│     ├─ Multi-modal content                                   │
│     ├─ Metadata preservation                                 │
│     └─ Message order                                         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Future Architecture Considerations

### Potential Enhancements

1. **Message Persistence**
   - Local storage for draft messages
   - IndexedDB for large histories
   - Service Worker for offline support

2. **Real-time Collaboration**
   - Multi-user presence
   - Typing indicators
   - Message synchronization

3. **Advanced Features**
   - Message search and filtering
   - Message threading/replies
   - Reactions and annotations
   - Export functionality

4. **Performance Optimization**
   - Virtual scrolling for large lists
   - Message archiving
   - Lazy loading of message details
   - Background message pruning

---

**Architecture Version**: 1.0.0
**Last Updated**: December 2024
**Maintainer**: Frontend Team
