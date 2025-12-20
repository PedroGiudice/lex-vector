
import React, { useState, useEffect } from 'react';
import { Terminal, FileEdit, FileText, Tool, ChevronDown, ChevronUp, CheckCircle, XCircle } from 'lucide-react';

const ToolCallDisplay = ({
  toolName,
  toolId,
  toolInput,
  toolResult,
  onFileOpen,
  autoExpand = false,
}) => {
  const [isInputExpanded, setIsInputExpanded] = useState(autoExpand);
  const [parsedInput, setParsedInput] = useState(null);
  const [inputError, setInputError] = useState(null);

  useEffect(() => {
    try {
      const parsed = JSON.parse(toolInput);
      setParsedInput(parsed);
      setInputError(null);
    } catch (e) {
      setParsedInput(toolInput); // Keep as string if not valid JSON
      setInputError("Invalid JSON input");
    }
  }, [toolInput]);

  const renderToolIcon = () => {
    switch (toolName) {
      case 'Bash':
        return <Terminal className="h-4 w-4 mr-2" />;
      case 'Edit':
        return <FileEdit className="h-4 w-4 mr-2" />;
      case 'Read':
        return <FileText className="h-4 w-4 mr-2" />;
      default:
        return <Tool className="h-4 w-4 mr-2" />;
    }
  };

  const getToolColorClass = () => {
    switch (toolName) {
      case 'Bash': return 'bg-blue-600';
      case 'Edit': return 'bg-purple-600';
      case 'Read': return 'bg-green-600';
      default: return 'bg-zinc-600';
    }
  };

  const renderSpecialInput = () => {
    if (!parsedInput) return null;

    switch (toolName) {
      case 'Bash':
        return (
          <div className="bg-zinc-900 text-green-400 p-3 rounded-md font-mono text-sm overflow-x-auto">
            <pre className="whitespace-pre-wrap">{parsedInput.command || JSON.stringify(parsedInput, null, 2)}</pre>
          </div>
        );
      case 'Edit':
        return (
          <div className="bg-zinc-700 p-3 rounded-md text-zinc-100 text-sm">
            <p className="font-semibold mb-2">File to edit: {parsedInput.path || 'N/A'}</p>
            <p className="mb-2 text-zinc-300">New content hint (actual diff not shown):</p>
            <div className="bg-zinc-800 text-zinc-200 p-2 rounded font-mono whitespace-pre-wrap">
              <pre>{parsedInput.content || JSON.stringify(parsedInput, null, 2)}</pre>
            </div>
          </div>
        );
      case 'Read':
        return (
          <div className="bg-zinc-700 p-3 rounded-md text-zinc-100 text-sm">
            <p className="font-semibold mb-2">File to read: {parsedInput.path || 'N/A'}</p>
            {onFileOpen && parsedInput.path && (
              <button
                onClick={() => onFileOpen(parsedInput.path)}
                className="mt-2 px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-xs"
              >
                Open File
              </button>
            )}
            {!parsedInput.path && <p className="text-red-400">File path not found in tool input.</p>}
          </div>
        );
      default:
        return (
          <div className="bg-zinc-800 p-3 rounded-md font-mono text-zinc-200 text-sm overflow-x-auto">
            <pre className="whitespace-pre-wrap">{JSON.stringify(parsedInput, null, 2)}</pre>
          </div>
        );
    }
  };

  return (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 mb-4 shadow-lg text-zinc-100">
      {/* Tool Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <span className={`flex items-center px-3 py-1 rounded-full text-xs font-semibold ${getToolColorClass()} text-white`}>
            {renderToolIcon()}
            {toolName}
          </span>
          <span className="ml-3 text-zinc-400 text-xs">ID: {toolId}</span>
        </div>
        <button
          onClick={() => setIsInputExpanded(!isInputExpanded)}
          className="text-zinc-400 hover:text-zinc-100 p-1 rounded-full hover:bg-zinc-700"
          aria-label={isInputExpanded ? "Collapse input" : "Expand input"}
        >
          {isInputExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>

      {/* Input Parameters Section */}
      {isInputExpanded && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold mb-2 text-zinc-300">Input Parameters:</h3>
          {inputError ? (
            <div className="bg-red-900 text-red-300 p-3 rounded-md text-sm">
              Error parsing input: {inputError}
              <div className="mt-2 bg-red-800 p-2 rounded font-mono whitespace-pre-wrap">
                <pre>{toolInput}</pre>
              </div>
            </div>
          ) : (
            renderSpecialInput()
          )}
        </div>
      )}

      {/* Result Section */}
      {toolResult && (
        <div>
          <h3 className="text-sm font-semibold mb-2 text-zinc-300">Result:</h3>
          <div
            className={`p-3 rounded-md text-sm flex items-start ${
              toolResult.isError ? 'bg-red-900 text-red-300 border border-red-700' : 'bg-green-900 text-green-300 border border-green-700'
            }`}
          >
            {toolResult.isError ? (
              <XCircle className="h-4 w-4 mr-2 flex-shrink-0 mt-0.5" />
            ) : (
              <CheckCircle className="h-4 w-4 mr-2 flex-shrink-0 mt-0.5" />
            )}
            <div className="font-mono whitespace-pre-wrap flex-grow overflow-x-auto">
              {toolResult.content || 'No result content provided.'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ToolCallDisplay;
