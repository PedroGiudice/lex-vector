import React from 'react';
import { Sparkles } from 'lucide-react';
import CCuiCodeBlock from './CCuiCodeBlock';
import CCuiThinkingBlock from './CCuiThinkingBlock';

/**
 * CCuiMessage - Single message display supporting user and assistant roles
 *
 * Features:
 * - User messages: right-aligned, bg-ccui-bg-hover with border
 * - Assistant messages: left-aligned, with CLAUDE header and Sparkles icon
 * - Parse code blocks (```language...```)
 * - Support 'thought' type using CCuiThinkingBlock
 *
 * @param {Object} props
 * @param {Object} props.message - Message object
 * @param {string} props.message.role - 'user' or 'assistant'
 * @param {string} props.message.content - Message content
 * @param {string} props.message.type - Message type ('thought', 'message', etc.)
 * @param {string} props.message.label - Label for thinking blocks
 * @param {number} props.message.duration - Duration for thinking blocks
 * @param {boolean} props.isStreaming - Whether message is currently streaming
 */
const CCuiMessage = ({ message, isStreaming = false }) => {
  const { role, content, type, label, duration } = message;

  // Handle thinking/reasoning blocks
  if (type === 'thought') {
    return (
      <CCuiThinkingBlock
        content={content}
        isStreaming={isStreaming}
        label={label}
        duration={duration}
      />
    );
  }

  // Parse content to extract code blocks
  const parseContent = (text) => {
    if (!text) return [];

    const parts = [];
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(text)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        const textContent = text.slice(lastIndex, match.index);
        if (textContent.trim()) {
          parts.push({
            type: 'text',
            content: textContent,
          });
        }
      }

      // Add code block
      parts.push({
        type: 'code',
        language: match[1] || 'plaintext',
        content: match[2].trim(),
      });

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      const textContent = text.slice(lastIndex);
      if (textContent.trim()) {
        parts.push({
          type: 'text',
          content: textContent,
        });
      }
    }

    return parts.length > 0 ? parts : [{ type: 'text', content: text }];
  };

  const contentParts = parseContent(content);

  // User message
  if (role === 'user') {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[80%] px-4 py-3 bg-ccui-bg-hover border border-ccui-border-tertiary rounded-lg">
          <div className="text-sm text-ccui-text-primary whitespace-pre-wrap leading-relaxed">
            {content}
            {isStreaming && (
              <span className="inline-block w-1.5 h-4 ml-1 bg-ccui-accent animate-pulse" />
            )}
          </div>
        </div>
      </div>
    );
  }

  // Assistant message
  return (
    <div className="flex flex-col mb-6">
      {/* Assistant header */}
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-4 h-4 text-ccui-accent" />
        <span className="text-xs font-semibold text-ccui-text-secondary tracking-wider">
          CLAUDE
        </span>
      </div>

      {/* Message content */}
      <div className="space-y-2">
        {contentParts.map((part, index) => {
          if (part.type === 'code') {
            return (
              <CCuiCodeBlock
                key={index}
                code={part.content}
                language={part.language}
                isStreaming={isStreaming && index === contentParts.length - 1}
              />
            );
          }

          return (
            <div
              key={index}
              className="text-sm text-ccui-text-primary whitespace-pre-wrap leading-relaxed"
            >
              {part.content}
              {isStreaming && index === contentParts.length - 1 && (
                <span className="inline-block w-1.5 h-4 ml-1 bg-ccui-accent animate-pulse" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CCuiMessage;
