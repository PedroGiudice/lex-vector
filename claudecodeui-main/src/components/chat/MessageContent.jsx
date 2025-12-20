import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

export default function MessageContent({ content }) {
  // Handle different content types
  if (!content) return null;

  // If content is a string, render as text
  if (typeof content === 'string') {
    return <div className="text-zinc-200 whitespace-pre-wrap">{content}</div>;
  }

  // If content is an array (Claude API format), render each block
  if (Array.isArray(content)) {
    return (
      <div className="space-y-2">
        {content.map((block, index) => (
          <ContentBlock key={index} block={block} />
        ))}
      </div>
    );
  }

  return <div className="text-zinc-200">{JSON.stringify(content)}</div>;
}

function ContentBlock({ block }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (text) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (block.type === 'text') {
    return <div className="text-zinc-200 whitespace-pre-wrap">{block.text}</div>;
  }

  if (block.type === 'code') {
    return (
      <div className="relative group">
        <pre className="bg-zinc-900 rounded-lg p-4 overflow-x-auto text-sm">
          <code className="text-zinc-300">{block.code || block.text}</code>
        </pre>
        <button
          onClick={() => handleCopy(block.code || block.text)}
          className="absolute top-2 right-2 p-1.5 rounded bg-zinc-700 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} className="text-zinc-400" />}
        </button>
      </div>
    );
  }

  if (block.type === 'tool_use') {
    return (
      <div className="bg-zinc-800/50 rounded-lg p-3 border border-zinc-700">
        <div className="text-xs text-zinc-500 mb-1">Tool: {block.name}</div>
        <pre className="text-xs text-zinc-400 overflow-x-auto">
          {JSON.stringify(block.input, null, 2)}
        </pre>
      </div>
    );
  }

  return null;
}
