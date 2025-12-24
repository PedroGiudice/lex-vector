import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, Folder, FileCode, FileJson, FileType, FileText, RefreshCw } from 'lucide-react';
import { api } from './utils/api';

interface TreeNode {
  name: string;
  type: 'file' | 'directory';
  children?: TreeNode[];
}

interface FileIconProps {
  name: string;
  className?: string;
}

const FileIcon: React.FC<FileIconProps> = ({ name, className = "w-4 h-4" }) => {
  const ext = name.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'py': return <FileCode className={`${className} text-yellow-500`} />;
    case 'tsx':
    case 'ts':
    case 'js':
    case 'jsx': return <FileCode className={`${className} text-[#d97757]`} />;
    case 'css': return <FileType className={`${className} text-pink-400`} />;
    case 'json': return <FileJson className={`${className} text-green-400`} />;
    case 'md': return <FileText className={`${className} text-blue-400`} />;
    default: return <FileText className={`${className} text-[#888]`} />;
  }
};

interface FileTreeItemProps {
  node: TreeNode;
  depth: number;
}

const FileTreeItem: React.FC<FileTreeItemProps> = ({ node, depth }) => {
  const [isOpen, setIsOpen] = useState(false);
  const paddingLeft = `${depth * 16 + 12}px`; // Increased indent

  // Handle click for folders
  const handleClick = () => {
    if (node.type === 'directory' || node.children) {
      setIsOpen(!isOpen);
    }
  };

  if (node.type === 'directory' || node.children) {
    return (
      <div>
        <div
          className="flex items-center py-1.5 hover:bg-[#1a1a1a] cursor-pointer text-[#a1a1aa] hover:text-[#d97757] transition-colors select-none text-sm group"
          style={{ paddingLeft }}
          onClick={handleClick}
        >
          {isOpen ? <ChevronDown className="w-3.5 h-3.5 mr-2 text-[#666] group-hover:text-[#d97757]" /> : <ChevronRight className="w-3.5 h-3.5 mr-2 text-[#666] group-hover:text-[#d97757]" />}
          <Folder className="w-4 h-4 mr-2 text-[#d97757]" />
          <span className="truncate font-medium group-hover:text-[#e3e1de]">{node.name}</span>
        </div>
        {isOpen && node.children?.map((child, idx) => (
          <FileTreeItem key={`${child.name}-${idx}`} node={child} depth={depth + 1} />
        ))}
      </div>
    );
  }

  return (
    <div
      className="flex items-center py-1.5 pr-2 hover:bg-[#1a1a1a] cursor-pointer text-[#a1a1aa] hover:text-[#e3e1de] transition-colors select-none text-sm group"
      style={{ paddingLeft }}
    >
      <div className="mr-2 opacity-80 group-hover:opacity-100 transition-opacity">
        <FileIcon name={node.name} className="w-4 h-4" />
      </div>
      <span className="truncate font-mono group-hover:text-[#d97757]">{node.name}</span>
    </div>
  );
};

export default function CCuiFileTree() {
  const [files, setFiles] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<TreeNode[]>('/api/projects');
      setFiles(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("File Tree Error:", e);
      setError("Failed to load file tree.");
      setFiles([
        {
          name: 'src',
          type: 'directory',
          children: [
            { name: 'App.tsx', type: 'file' },
            {
              name: 'components', type: 'directory', children: [
                { name: 'CCuiLayout.jsx', type: 'file' }
              ]
            }
          ]
        },
        { name: 'package.json', type: 'file' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  if (loading) {
    return (
      <div className="p-4 flex items-center justify-center text-[#a1a1aa]">
        <RefreshCw className="w-5 h-5 animate-spin" />
      </div>
    );
  }

  if (error && files.length === 0) {
    return (
      <div className="p-4 text-center">
        <p className="text-xs text-red-400 mb-2">{error}</p>
        <button onClick={fetchFiles} className="text-xs underline text-[#a1a1aa]">Retry</button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-2 py-2 mb-2 border-b border-[#27272a]/50">
        <span className="text-xs font-bold text-[#6b6a67] uppercase tracking-wider">Project Files</span>
        <button onClick={fetchFiles} className="text-[#6b6a67] hover:text-[#d97757]">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {files.map((node, i) => (
          <FileTreeItem key={`${node.name}-${i}`} node={node} depth={0} />
        ))}
      </div>
    </div>
  );
}
