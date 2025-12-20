import { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import ThinkingIndicator from './ThinkingIndicator';

export default function MessageList({
  messages,
  isProcessing,
  autoScroll = true
}) {
  const containerRef = useRef(null);
  const bottomRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto px-4 py-6"
    >
      <div className="max-w-4xl mx-auto space-y-1">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          messages.map((message, index) => (
            <MessageBubble
              key={message.id || index}
              message={message}
              isUser={message.role === 'user' || message.type === 'user'}
            />
          ))
        )}

        {isProcessing && <ThinkingIndicator />}

        {/* Scroll anchor */}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full py-20 text-center">
      <div className="w-16 h-16 bg-orange-500/10 rounded-2xl flex items-center justify-center mb-4">
        <svg
          className="w-8 h-8 text-orange-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-zinc-300 mb-2">
        Start a conversation
      </h3>
      <p className="text-sm text-zinc-500 max-w-sm">
        Describe your task or enter a command to get started with Claude.
      </p>
    </div>
  );
}
