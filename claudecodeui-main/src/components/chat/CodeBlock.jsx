import React, { useState, useCallback } from 'react';
import { Copy, Check } from 'lucide-react';

/**
 * CodeBlock Component
 *
 * A reusable code block component that handles both inline and block code rendering.
 * Extracted from ChatInterface.jsx markdownComponents.code pattern.
 *
 * Usage:
 * ```jsx
 * import CodeBlock from '@/components/chat/CodeBlock';
 *
 * // Block code with language
 * <CodeBlock className="language-javascript">
 *   const greeting = "Hello World";
 *   console.log(greeting);
 * </CodeBlock>
 *
 * // Inline code
 * <CodeBlock inline>npm install</CodeBlock>
 *
 * // Used with react-markdown
 * <ReactMarkdown components={{ code: CodeBlock }}>
 *   {markdownContent}
 * </ReactMarkdown>
 * ```
 */
export default function CodeBlock({ node, inline, className, children, ...props }) {
  const [copied, setCopied] = useState(false);

  // Extract text content from children
  const raw = Array.isArray(children) ? children.join('') : String(children ?? '');

  // Detect if content is multiline
  const looksMultiline = /[\r\n]/.test(raw);

  // Determine if should render as inline code
  const inlineDetected = inline || (node && node.type === 'inlineCode');
  const shouldInline = inlineDetected || !looksMultiline;

  // Extract language from className (e.g., "language-javascript" -> "javascript")
  const language = className?.match(/language-(\w+)/)?.[1];

  // Copy handler with clipboard API and fallback
  const handleCopy = useCallback(() => {
    const doSet = () => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    };

    try {
      if (navigator?.clipboard?.writeText) {
        navigator.clipboard
          .writeText(raw)
          .then(doSet)
          .catch(() => {
            // Fallback to execCommand
            fallbackCopy(raw, doSet);
          });
      } else {
        // Fallback for older browsers
        fallbackCopy(raw, doSet);
      }
    } catch {
      fallbackCopy(raw, doSet);
    }
  }, [raw]);

  // Fallback copy using textarea + execCommand
  const fallbackCopy = (text, callback) => {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
    } catch {}
    document.body.removeChild(ta);
    callback();
  };

  // Render inline code
  if (shouldInline) {
    return (
      <code
        className={`font-mono text-[0.9em] px-1.5 py-0.5 rounded-md bg-gray-100 text-gray-900 border border-gray-200 dark:bg-gray-800/60 dark:text-gray-100 dark:border-gray-700 whitespace-pre-wrap break-words ${
          className || ''
        }`}
        {...props}
      >
        {children}
      </code>
    );
  }

  // Render block code with copy button
  return (
    <div className="relative group my-2">
      {/* Copy button - shows on hover */}
      <button
        type="button"
        onClick={handleCopy}
        className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 focus:opacity-100 active:opacity-100 transition-opacity text-xs px-2 py-1 rounded-md bg-gray-700/80 hover:bg-gray-700 text-white border border-gray-600"
        title={copied ? 'Copied' : 'Copy code'}
        aria-label={copied ? 'Copied' : 'Copy code'}
      >
        {copied ? (
          <span className="flex items-center gap-1">
            <Check className="w-3.5 h-3.5" />
            Copied
          </span>
        ) : (
          <span className="flex items-center gap-1">
            <Copy className="w-3.5 h-3.5" />
            Copy
          </span>
        )}
      </button>

      {/* Language label (optional) */}
      {language && (
        <div className="absolute top-2 left-3 text-xs text-gray-400 uppercase tracking-wider font-mono opacity-60">
          {language}
        </div>
      )}

      {/* Code block */}
      <pre className="bg-gray-900 dark:bg-gray-900 border border-gray-700/40 rounded-lg p-3 overflow-x-auto">
        <code
          className={`text-gray-100 dark:text-gray-100 text-sm font-mono ${className || ''}`}
          {...props}
        >
          {children}
        </code>
      </pre>
    </div>
  );
}
