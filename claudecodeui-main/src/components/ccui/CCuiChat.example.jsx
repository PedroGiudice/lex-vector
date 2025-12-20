import React, { useState } from 'react';
import {
  CCuiCodeBlock,
  CCuiThinkingBlock,
  CCuiChatInput,
  CCuiMessage
} from './index';

/**
 * Example usage of CCui Chat Components
 * 
 * This demonstrates how to use all the chat components together
 * in a complete chat interface.
 */
const CCuiChatExample = () => {
  const [messages, setMessages] = useState([
    {
      role: 'user',
      content: 'Can you show me a React component example?'
    },
    {
      role: 'assistant',
      type: 'thought',
      content: 'Let me think about the best way to demonstrate a React component...',
      label: 'Thinking',
      duration: 1234
    },
    {
      role: 'assistant',
      content: `Here's a simple React component example:

\`\`\`jsx
import React, { useState } from 'react';

const Counter = () => {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
};

export default Counter;
\`\`\`

This component demonstrates state management using the useState hook.`
    }
  ]);

  const [isStreaming, setIsStreaming] = useState(false);

  const handleSend = (message) => {
    setMessages([...messages, { role: 'user', content: message }]);
    
    // Simulate assistant response
    setIsStreaming(true);
    setTimeout(() => {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'This is a simulated response to demonstrate the chat interface.'
        }
      ]);
      setIsStreaming(false);
    }, 1000);
  };

  const handleActionsClick = () => {
    console.log('Actions clicked');
  };

  const handleHistoryClick = () => {
    console.log('History clicked');
  };

  return (
    <div className="flex flex-col h-screen bg-ccui-bg-primary">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.map((message, index) => (
          <CCuiMessage
            key={index}
            message={message}
            isStreaming={isStreaming && index === messages.length - 1}
          />
        ))}
      </div>

      {/* Input area */}
      <div className="border-t border-ccui-border-tertiary p-6">
        <CCuiChatInput
          onSend={handleSend}
          disabled={isStreaming}
          placeholder="Ask Claude anything..."
          onActionsClick={handleActionsClick}
          onHistoryClick={handleHistoryClick}
        />
      </div>
    </div>
  );
};

// Individual component examples

const CodeBlockExample = () => (
  <div className="p-6 bg-ccui-bg-primary">
    <h2 className="text-ccui-text-primary mb-4">Code Block Example</h2>
    <CCuiCodeBlock
      code={`function hello() {
  console.log("Hello, world!");
}`}
      language="javascript"
      isStreaming={false}
    />
  </div>
);

const ThinkingBlockExample = () => (
  <div className="p-6 bg-ccui-bg-primary">
    <h2 className="text-ccui-text-primary mb-4">Thinking Block Example</h2>
    <CCuiThinkingBlock
      content="I'm analyzing the code structure and considering the best approach to solve this problem. Let me break it down step by step..."
      isStreaming={false}
      label="Reasoning"
      duration={2500}
    />
  </div>
);

export default CCuiChatExample;
export { CodeBlockExample, ThinkingBlockExample };
