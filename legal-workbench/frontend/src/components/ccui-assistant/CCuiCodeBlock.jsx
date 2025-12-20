import React, { useLayoutEffect, useRef, useState } from 'react';
import { Check, Copy } from 'lucide-react';

/**
 * CCuiCodeBlock - Code block with Prism.js syntax highlighting
 *
 * Features:
 * - Prism.js syntax highlighting
 * - Copy to clipboard functionality
 * - Streaming indicator with coral cursor
 * - Support for multiple languages
 *
 * @param {Object} props
 * @param {string} props.code - The code content to display
 * @param {string} props.language - Programming language for syntax highlighting
 * @param {boolean} props.isStreaming - Whether content is currently streaming
 */
const CCuiCodeBlock = ({ code, language = 'javascript', isStreaming = false }) => {
  const codeRef = useRef(null);
  const [copied, setCopied] = useState(false);

  // Apply Prism highlighting after render
  useLayoutEffect(() => {
    if (codeRef.current && window.Prism) {
      window.Prism.highlightElement(codeRef.current);
    }
  }, [code]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  return (
    <div className="relative group my-4 rounded-lg overflow-hidden border border-ccui-border-tertiary">
      {/* Language label and copy button */}
      <div className="flex items-center justify-between px-4 py-2 bg-ccui-bg-tertiary border-b border-ccui-border-tertiary">
        <span className="text-xs text-ccui-text-secondary font-mono uppercase">
          {language}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2 py-1 text-xs text-ccui-text-secondary hover:text-ccui-text-primary transition-colors rounded"
          aria-label="Copy code to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-green-500" />
              <span className="text-green-500">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code content */}
      <div className="relative overflow-x-auto bg-ccui-bg-primary">
        <pre className="!m-0 !p-4 !bg-transparent">
          <code
            ref={codeRef}
            className={`ccui-code language-${language} !text-sm ${
              isStreaming ? 'streaming-cursor' : ''
            }`}
          >
            {code}
          </code>
        </pre>

        {/* Streaming cursor */}
        {isStreaming && (
          <span className="absolute bottom-4 right-4 w-2 h-4 bg-ccui-accent animate-pulse" />
        )}
      </div>
    </div>
  );
};

export default CCuiCodeBlock;
