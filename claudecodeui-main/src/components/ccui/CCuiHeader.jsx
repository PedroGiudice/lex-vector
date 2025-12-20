import React from 'react';
import { Folder, Cpu, Search, Settings } from 'lucide-react';

/**
 * CCuiHeader - Minimal header with traffic lights, project path, and model selector
 *
 * @param {Object} props
 * @param {string} props.projectPath - Current project path
 * @param {string} props.currentModel - Current AI model name
 * @param {Function} props.onSettingsClick - Settings button click handler
 * @param {Function} props.onSearchClick - Search button click handler
 */
const CCuiHeader = ({
  projectPath = 'No Project',
  currentModel = 'claude-sonnet-4-5',
  onSettingsClick,
  onSearchClick
}) => {
  return (
    <header className="h-12 bg-ccui-bg-secondary border-b border-ccui-border-primary flex items-center justify-between px-4">
      {/* Left: Traffic Lights */}
      <div className="flex items-center gap-2">
        <div className="flex gap-1.5">
          <button
            className="w-3 h-3 rounded-full bg-red-500 hover:bg-red-400 transition-colors"
            aria-label="Close"
          />
          <button
            className="w-3 h-3 rounded-full bg-yellow-500 hover:bg-yellow-400 transition-colors"
            aria-label="Minimize"
          />
          <button
            className="w-3 h-3 rounded-full bg-green-500 hover:bg-green-400 transition-colors"
            aria-label="Maximize"
          />
        </div>
      </div>

      {/* Center: Project Path */}
      <div className="flex items-center gap-2 text-ccui-text-secondary">
        <Folder size={16} />
        <span className="text-sm font-medium text-ccui-text-primary truncate max-w-md">
          {projectPath}
        </span>
      </div>

      {/* Right: Model Selector and Actions */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1 rounded bg-ccui-bg-primary border border-ccui-border-primary">
          <Cpu size={14} className="text-ccui-text-muted" />
          <span className="text-xs text-ccui-text-secondary font-mono">
            {currentModel}
          </span>
        </div>

        <button
          onClick={onSearchClick}
          className="p-1.5 rounded hover:bg-ccui-bg-primary transition-colors text-ccui-text-secondary hover:text-ccui-text-primary"
          aria-label="Search"
        >
          <Search size={16} />
        </button>

        <button
          onClick={onSettingsClick}
          className="p-1.5 rounded hover:bg-ccui-bg-primary transition-colors text-ccui-text-secondary hover:text-ccui-text-primary"
          aria-label="Settings"
        >
          <Settings size={16} />
        </button>
      </div>
    </header>
  );
};

export default CCuiHeader;
