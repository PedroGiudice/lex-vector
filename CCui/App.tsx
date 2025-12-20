import React, { useState, useEffect, useRef, useLayoutEffect } from 'react';
import { 
  Terminal, 
  Folder, 
  Settings, 
  ChevronRight, 
  ChevronDown,
  Command, 
  Copy, 
  Check, 
  Loader2,
  Sparkles,
  Activity,
  ArrowUp,
  Trash2,
  Edit2,
  Plus,
  Clock,
  DollarSign,
  FileCode,
  FileJson,
  FileType,
  Image,
  Search,
  MoreVertical,
  Cpu,
  Files,
  GitGraph,
  Bug,
  X,
  FileText,
  MessageSquare
} from 'lucide-react';

// Declaration for global Prism object from CDN
declare global {
  interface Window {
    Prism: any;
  }
}

// --- HELPER COMPONENT: CODE BLOCK ---
const CodeBlock: React.FC<{ code: string; language?: string; isStreaming?: boolean }> = ({ code, language = 'javascript', isStreaming = false }) => {
  const [copied, setCopied] = useState(false);
  const codeRef = useRef<HTMLElement>(null);

  useLayoutEffect(() => {
    if (window.Prism && codeRef.current) {
      window.Prism.highlightElement(codeRef.current);
    }
  }, [code, language]);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-2 rounded-md overflow-hidden border border-[#333] bg-[#0c0c0c] shadow-sm">
      <div className="flex items-center justify-between px-3 py-1 bg-[#1a1a1a] border-b border-[#333]">
        <div className="flex items-center space-x-2">
           <span className="text-[10px] text-[#888] font-mono lowercase">{language}</span>
        </div>
        <button 
          onClick={handleCopy}
          className="flex items-center space-x-1 text-[10px] text-[#666] hover:text-[#e0e0e0] transition-colors"
        >
          {copied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <div className="relative">
        <pre className="!m-0 !p-3 !bg-[#09090b] !text-[11px] overflow-x-auto custom-scrollbar font-mono leading-relaxed">
          <code ref={codeRef} className={`language-${language} !bg-transparent !text-shadow-none`}>
            {code}
          </code>
          {isStreaming && (
             <span className="inline-block w-1.5 h-3 bg-[#d97757] align-middle ml-1 animate-pulse"></span>
          )}
        </pre>
      </div>
    </div>
  );
};

// --- HELPER: FILE ICON ---
const FileIcon: React.FC<{ name: string; className?: string }> = ({ name, className = "w-4 h-4" }) => {
    const ext = name.split('.').pop()?.toLowerCase();
    
    switch(ext) {
        case 'py': return <FileCode className={`${className} text-yellow-500`} />;
        case 'tsx':
        case 'ts':
        case 'js':
        case 'jsx': return <FileCode className={`${className} text-blue-400`} />;
        case 'css':
        case 'scss': return <FileType className={`${className} text-pink-400`} />;
        case 'html': return <FileType className={`${className} text-orange-400`} />;
        case 'json':
        case 'yaml':
        case 'yml': return <FileJson className={`${className} text-green-400`} />;
        case 'md':
        case 'txt': return <FileText className={`${className} text-gray-400`} />;
        case 'png':
        case 'jpg':
        case 'svg': return <Image className={`${className} text-purple-400`} />;
        default: return <FileText className={`${className} text-gray-500`} />;
    }
};

// --- HELPER: COLLAPSIBLE THINKING BLOCK ---
const ThinkingBlock: React.FC<{ content: string; isStreaming?: boolean; label?: string; duration?: string }> = ({ content, isStreaming, label = "Reasoning", duration }) => {
    const [isOpen, setIsOpen] = useState(true);

    return (
        <div className="mb-2 group">
            <div 
                className="flex items-center gap-2 cursor-pointer select-none py-1"
                onClick={() => setIsOpen(!isOpen)}
            >
                <div className="w-3.5 h-3.5 flex items-center justify-center">
                     {isStreaming ? (
                         <Loader2 className="w-3 h-3 text-[#d97757] animate-spin" />
                     ) : (
                         isOpen ? <ChevronDown className="w-3 h-3 text-[#666]" /> : <ChevronRight className="w-3 h-3 text-[#666]" />
                     )}
                </div>
                <span className={`text-[10px] font-mono font-medium tracking-tight ${isStreaming ? 'text-[#e0e0e0]' : 'text-[#666]'}`}>
                    {label}
                </span>
                {duration && <span className="text-[10px] text-[#444] font-mono ml-auto">{duration}</span>}
            </div>
            
            {isOpen && (
                <div className="pl-5 pr-2 py-1">
                    <div className="text-[11px] text-[#666] font-mono border-l border-[#222] pl-3 py-1 leading-relaxed">
                        {content}
                        {isStreaming && <span className="inline-block w-1.5 h-3 bg-[#d97757] ml-1 animate-pulse" />}
                    </div>
                </div>
            )}
        </div>
    );
};

// --- HELPER: SIDEBAR ICON ---
const SidebarIcon: React.FC<{ icon: React.ElementType; active: boolean; onClick: () => void }> = ({ icon: Icon, active, onClick }) => (
    <button 
        onClick={onClick}
        className={`w-full p-3 flex justify-center transition-all duration-200 relative group ${active ? 'text-[#e0e0e0]' : 'text-[#555] hover:text-[#888]'}`}
    >
        <Icon className="w-5 h-5" strokeWidth={1.5} />
        {active && <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-[#d97757]"></div>}
    </button>
);

// --- HELPER: FILE TREE COMPONENT ---
type FileNode = {
  id: string;
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
};

interface FileTreeItemProps {
    node: FileNode;
    depth: number;
    onDelete?: (id: string) => void;
    onEdit?: (id: string, newName: string) => void;
}

const FileTreeItem: React.FC<FileTreeItemProps> = ({ node, depth, onDelete, onEdit }) => {
  const [isOpen, setIsOpen] = useState(depth === 0 || node.name === 'src');
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(node.name);
  const paddingLeft = `${depth * 12 + 12}px`;

  const handleEditSubmit = (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
          if (onEdit) onEdit(node.id, editName);
          setIsEditing(false);
      }
  };

  if (node.type === 'folder') {
    return (
      <div>
        <div 
          className="flex items-center py-1 hover:bg-[#1a1a1a] cursor-pointer text-[#888] hover:text-[#e0e0e0] transition-colors select-none text-[11px]"
          style={{ paddingLeft }}
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? <ChevronDown className="w-3 h-3 mr-1.5 text-[#555]" /> : <ChevronRight className="w-3 h-3 mr-1.5 text-[#555]" />}
          <Folder className="w-3.5 h-3.5 mr-1.5 text-[#d97757]" />
          <span className="truncate font-medium">{node.name}</span>
        </div>
        {isOpen && node.children?.map(child => (
          <FileTreeItem key={child.id} node={child} depth={depth + 1} onDelete={onDelete} onEdit={onEdit} />
        ))}
      </div>
    );
  }

  return (
    <div 
      className="flex items-center justify-between py-1 pr-2 hover:bg-[#1a1a1a] cursor-pointer text-[#888] hover:text-[#e0e0e0] transition-colors select-none text-[11px] group"
      style={{ paddingLeft }}
    >
      <div className="flex items-center flex-1 min-w-0">
          <div className="mr-1.5 opacity-70 group-hover:opacity-100 transition-opacity">
            <FileIcon name={node.name} className="w-3.5 h-3.5" />
          </div>
          {isEditing ? (
              <input 
                  value={editName} 
                  onChange={(e) => setEditName(e.target.value)}
                  onKeyDown={handleEditSubmit}
                  className="bg-[#111] text-white border border-[#333] px-1 py-0.5 w-full focus:outline-none focus:border-[#d97757] rounded-sm font-mono text-[11px]"
                  autoFocus
                  onBlur={() => setIsEditing(false)}
              />
          ) : (
              <span className="truncate font-mono" onDoubleClick={() => setIsEditing(true)}>{node.name}</span>
          )}
      </div>
      <div className="hidden group-hover:flex items-center space-x-1 ml-2">
          <Edit2 className="w-3 h-3 text-[#555] hover:text-[#d97757]" onClick={() => setIsEditing(true)} />
          <Trash2 className="w-3 h-3 text-[#555] hover:text-red-500" onClick={() => onDelete && onDelete(node.id)} />
      </div>
    </div>
  );
};

// --- TYPES ---
interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string; // Raw content
  type?: 'text' | 'thought' | 'bash';
  isStreaming?: boolean;
  label?: string;
  duration?: string;
  meta?: any; // Extra data for bash commands etc
}

// --- APP COMPONENT ---
const App: React.FC = () => {
  // State
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, role: 'assistant', content: 'Claude Code CLI wrapper initialized.\nSession started in /Users/dev/project-alpha', type: 'text' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sidebarView, setSidebarView] = useState<'explorer' | 'history' | 'search' | 'git' | 'debug'>('history');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<number | null>(null);

  // Status Metrics
  const [cost, setCost] = useState(0.042);
  const [context, setContext] = useState(14); // %

  // Chat History Data
  const historyGroups = [
    {
        label: 'Today',
        items: [
            { id: 101, title: 'Refactor App.tsx Structure', time: '10:23 AM', active: true },
            { id: 102, title: 'Fix Tailwind Config', time: '9:41 AM', active: false }
        ]
    },
    {
        label: 'Yesterday',
        items: [
            { id: 103, title: 'Component Library Setup', time: '2:15 PM', active: false },
            { id: 104, title: 'Initial Project Scaffold', time: '11:00 AM', active: false }
        ]
    },
    {
        label: 'Previous 7 Days',
        items: [
            { id: 105, title: 'Git Integration Logic', time: 'Mon', active: false },
            { id: 106, title: 'Dependencies Audit', time: 'Mon', active: false }
        ]
    }
  ];

  // File Tree Data
  const [fileTree, setFileTree] = useState<FileNode[]>([
      { id: 'root', name: 'project-alpha', type: 'folder', children: [
          { id: 'f1', name: 'src', type: 'folder', children: [
              { id: 'f1-1', name: 'App.tsx', type: 'file' },
              { id: 'f1-2', name: 'index.tsx', type: 'file' },
              { id: 'f1-3', name: 'utils.ts', type: 'file' },
              { id: 'f1-4', name: 'components', type: 'folder', children: [
                  { id: 'c1', name: 'Header.tsx', type: 'file' },
                  { id: 'c2', name: 'Sidebar.tsx', type: 'file' }
              ]}
          ]},
          { id: 'f2', name: 'package.json', type: 'file' },
          { id: 'f3', name: 'tsconfig.json', type: 'file' },
          { id: 'f4', name: 'README.md', type: 'file' }
      ]}
  ]);

  // Auto-scroll
  useEffect(() => {
    if (messagesEndRef.current) {
        setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 50);
    }
  }, [messages, isTyping]);

  // -- STREAMING HELPER --
  const streamText = (messageId: number, fullText: string, speed = 8) => {
      let currentIndex = 0;
      if (abortControllerRef.current) window.clearInterval(abortControllerRef.current);
      
      const interval = window.setInterval(() => {
          if (currentIndex < fullText.length) {
              const remaining = fullText.length - currentIndex;
              const chunkSize = Math.min(remaining, Math.random() > 0.8 ? 3 : 1);
              
              setMessages(prev => prev.map(m => 
                  m.id === messageId 
                  ? { ...m, content: fullText.slice(0, currentIndex + chunkSize) } 
                  : m
              ));
              currentIndex += chunkSize;
          } else {
              window.clearInterval(interval);
              setIsTyping(false);
              setMessages(prev => prev.map(m => m.id === messageId ? { ...m, isStreaming: false } : m));
              setCost(c => c + 0.003); // Simulate cost update
              setContext(c => Math.min(100, c + 1)); // Simulate context update
          }
      }, speed);
      
      abortControllerRef.current = interval;
  };

  const handleSendMessage = () => {
    if (!input.trim()) return;
    
    // Reset
    if (abortControllerRef.current) {
        window.clearInterval(abortControllerRef.current);
        setIsTyping(false);
    }

    const cmd = input;
    const userMsg: Message = { id: Date.now(), role: 'user', content: cmd };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    // Simulation Sequence
    // 1. Thinking
    const thoughtId = Date.now() + 1;
    setTimeout(() => {
      setMessages(prev => [...prev, { 
          id: thoughtId, 
          role: 'assistant', 
          content: '', 
          type: 'thought',
          label: 'Planning',
          isStreaming: true
      }]);
      streamText(thoughtId, "Analyzing project structure and checking for existing patterns in src/components...", 25);
    }, 400);

    // 2. Response (with Code)
    setTimeout(() => {
        // Mark thought as done
        setMessages(prev => prev.map(m => m.id === thoughtId ? { ...m, isStreaming: false, duration: '1.2s' } : m));

        const responseId = Date.now() + 3;
        const responseText = `I'll create a new component for the navigation. Here's the plan:

1. Create \`src/components/Navigation.tsx\`
2. Update \`App.tsx\` to include it.

Execuiting:
\`\`\`bash
touch src/components/Navigation.tsx
\`\`\`

Here is the initial implementation:

\`\`\`tsx
import React from 'react';
import { Home, Settings, User } from 'lucide-react';

export const Navigation = () => {
  return (
    <nav className="flex items-center gap-4 p-4 border-b">
      <Home className="w-5 h-5" />
      <span className="font-bold">Dashboard</span>
      <div className="ml-auto flex gap-2">
         <Settings className="w-4 h-4" />
         <User className="w-4 h-4" />
      </div>
    </nav>
  );
};
\`\`\`
`;
        setMessages(prev => [...prev, {
            id: responseId,
            role: 'assistant',
            content: '', // Will stream into here
            type: 'text',
            isStreaming: true
        }]);
        streamText(responseId, responseText, 5);
        
        // Simulate file system update
        setTimeout(() => {
            const newFile: FileNode = { id: `new-${Date.now()}`, name: 'Navigation.tsx', type: 'file' };
            setFileTree(prev => {
                const newTree = [...prev];
                // Deep find src/components
                // For demo simplified:
                const src = newTree.find(n => n.name === 'src');
                const comps = src?.children?.find(n => n.name === 'components');
                if (comps && comps.children) {
                    comps.children.push(newFile);
                }
                return newTree;
            });
        }, 3000);

    }, 2500);
  };

  // --- DRAG & DROP ---
  const handleDrop = (e: React.DragEvent) => {
      e.preventDefault();
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
          const newFiles: FileNode[] = files.map((f: any) => ({
              id: `dropped-${Date.now()}-${f.name}`,
              name: f.name,
              type: 'file'
          }));
          
          setFileTree(prev => {
              const root = prev.find(n => n.id === 'root');
              if (root) {
                  root.children = [...(root.children || []), ...newFiles];
              }
              return [...prev];
          });
          
          setMessages(prev => [...prev, {
              id: Date.now(),
              role: 'assistant',
              content: `Added ${files.length} file(s) to project context.`,
              type: 'text'
          }]);
      }
  };

  // --- RENDER TEXT WITH CODE BLOCKS ---
  const renderFormattedContent = (content: string, isStreaming: boolean) => {
      if (!content) return null;
      
      const parts = content.split(/(```[\s\S]*?```)/g);
      
      return parts.map((part, index) => {
          if (part.startsWith('```')) {
              // Extract language
              const match = part.match(/```(\w*)\n([\s\S]*?)```/);
              if (match) {
                  const lang = match[1] || 'text';
                  const code = match[2];
                  return <CodeBlock key={index} code={code} language={lang} />;
              }
          }
          // Normal Text (handled with simple whitespace preservation)
          return <div key={index} className="whitespace-pre-wrap mb-1 text-[#d1d5db] font-normal">{part}</div>;
      });
  };

  return (
    <div 
      className="flex flex-col h-screen w-full bg-[#000000] text-[#e0e0e0] font-sans overflow-hidden selection:bg-[#d97757]/30"
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      
      {/* --- HEADER --- */}
      <header className="flex-none h-10 bg-[#050505] border-b border-[#1a1a1a] flex items-center justify-between px-4 z-50 select-none">
        <div className="flex items-center gap-3">
           <div className="flex gap-2 group cursor-pointer">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 group-hover:bg-red-500 border border-red-500/50 transition-colors"></div>
              <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 group-hover:bg-yellow-500 border border-yellow-500/50 transition-colors"></div>
              <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 group-hover:bg-green-500 border border-green-500/50 transition-colors"></div>
           </div>
           <div className="h-4 w-[1px] bg-[#222] mx-1"></div>
           <div className="flex items-center gap-2 text-xs font-medium text-[#888]">
              <Folder className="w-3 h-3" />
              <span>~/project-alpha</span>
           </div>
        </div>
        
        <div className="flex items-center gap-4 text-[10px] font-mono text-[#444]">
            <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#111] border border-[#222]">
                <Cpu className="w-3 h-3 text-[#d97757]" />
                <span className="text-[#888]">Claude 3.7 Sonnet</span>
            </div>
            <div className="flex items-center gap-3">
                <Search className="w-3.5 h-3.5 hover:text-[#d97757] cursor-pointer transition-colors" />
                <Settings className="w-3.5 h-3.5 hover:text-[#d97757] cursor-pointer transition-colors" />
            </div>
        </div>
      </header>

      {/* --- MAIN LAYOUT --- */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* ICON RAIL */}
        <aside className="w-12 bg-[#050505] border-r border-[#1a1a1a] flex flex-col items-center py-2 z-50">
            <SidebarIcon icon={MessageSquare} active={sidebarView === 'history'} onClick={() => setSidebarView('history')} />
            <SidebarIcon icon={Files} active={sidebarView === 'explorer'} onClick={() => setSidebarView('explorer')} />
            <SidebarIcon icon={Search} active={sidebarView === 'search'} onClick={() => setSidebarView('search')} />
            <SidebarIcon icon={GitGraph} active={sidebarView === 'git'} onClick={() => setSidebarView('git')} />
            <SidebarIcon icon={Bug} active={sidebarView === 'debug'} onClick={() => setSidebarView('debug')} />
            <div className="mt-auto mb-2">
                 <SidebarIcon icon={Settings} active={false} onClick={() => {}} />
            </div>
        </aside>

        {/* SIDEBAR PANEL */}
        <aside className="w-60 bg-[#050505] border-r border-[#1a1a1a] flex flex-col hidden md:flex z-40">
           <div className="h-9 border-b border-[#1a1a1a] flex items-center justify-between px-3">
               <span className="text-[10px] uppercase font-bold tracking-wider text-[#666]">{sidebarView === 'history' ? 'Chats' : sidebarView}</span>
               <div className="flex gap-1">
                   {sidebarView === 'history' ? (
                       <Edit2 className="w-3.5 h-3.5 text-[#444] hover:text-[#e0e0e0] cursor-pointer" />
                   ) : (
                       <Plus className="w-3.5 h-3.5 text-[#444] hover:text-[#e0e0e0] cursor-pointer" />
                   )}
                   <MoreVertical className="w-3.5 h-3.5 text-[#444] hover:text-[#e0e0e0] cursor-pointer" />
               </div>
           </div>
           
           <div className="flex-1 overflow-y-auto custom-scrollbar">
              {sidebarView === 'history' && (
                  <div className="flex flex-col py-2">
                      <div className="px-2 mb-3">
                         <button 
                            onClick={() => {
                                setMessages([]); 
                                setInput(''); 
                                // Reset logic simulation
                            }}
                            className="w-full flex items-center justify-center gap-2 bg-[#1a1a1a] hover:bg-[#222] text-[#e0e0e0] text-[11px] py-1.5 rounded border border-[#333] transition-colors group"
                         >
                            <Plus className="w-3.5 h-3.5 text-[#666] group-hover:text-[#d97757]" />
                            <span>New Chat</span>
                         </button>
                      </div>
                      {historyGroups.map(group => (
                         <div key={group.label} className="mb-4">
                            <div className="px-3 mb-1.5 text-[10px] font-bold text-[#444] uppercase tracking-wider">{group.label}</div>
                            {group.items.map(item => (
                               <div key={item.id} className={`px-3 py-2 cursor-pointer border-l-2 transition-all ${item.active ? 'border-[#d97757] bg-[#111]' : 'border-transparent hover:bg-[#0f0f0f]'}`}>
                                   <div className={`text-[11px] truncate ${item.active ? 'text-[#e0e0e0] font-medium' : 'text-[#888]'}`}>{item.title}</div>
                                   <div className="text-[10px] text-[#444] mt-0.5">{item.time}</div>
                               </div>
                            ))}
                         </div>
                      ))}
                  </div>
              )}

              {sidebarView === 'explorer' && (
                  <div className="p-2">
                      {fileTree.map(node => (
                          <FileTreeItem key={node.id} node={node} depth={0} />
                      ))}
                  </div>
              )}
              {sidebarView === 'search' && (
                  <div className="p-2 text-center text-[#444] text-xs">
                      <Search className="w-8 h-8 mx-auto mb-2 opacity-20" />
                      <p>No results found</p>
                  </div>
              )}
              {sidebarView === 'git' && (
                   <div className="p-2 text-center text-[#444] text-xs">
                      <GitGraph className="w-8 h-8 mx-auto mb-2 opacity-20" />
                      <p>No changes detected</p>
                  </div>
              )}
              {sidebarView === 'debug' && (
                   <div className="p-2 text-center text-[#444] text-xs">
                      <Bug className="w-8 h-8 mx-auto mb-2 opacity-20" />
                      <p>No active session</p>
                  </div>
              )}
           </div>
        </aside>

        {/* CHAT INTERFACE */}
        <main className="flex-1 flex flex-col relative bg-[#000000]">
           
           {/* Messages Area */}
           <div className="flex-1 overflow-y-auto p-4 md:p-8 pb-32 custom-scrollbar">
              <div className="max-w-3xl mx-auto space-y-6">
                 {messages.map((msg) => (
                    <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} animate-fade-in`}>
                       
                       {/* ASSISTANT */}
                       {msg.role === 'assistant' && (
                          <div className="w-full max-w-3xl pl-1">
                             
                             {/* Slim Assistant Header */}
                             <div className="flex items-center gap-2 mb-1">
                                <Sparkles className="w-3.5 h-3.5 text-[#d97757]" />
                                <span className="text-[10px] font-bold text-[#888] tracking-wide">CLAUDE</span>
                             </div>

                             {/* Thinking Component */}
                             {msg.type === 'thought' && (
                                 <ThinkingBlock 
                                    content={msg.content} 
                                    isStreaming={msg.isStreaming} 
                                    label={msg.label} 
                                    duration={msg.duration}
                                 />
                             )}

                             {/* Text Content */}
                             {msg.type === 'text' && (
                                 <div className="text-[13px] leading-relaxed text-[#d1d5db] font-normal">
                                     {renderFormattedContent(msg.content, !!msg.isStreaming)}
                                 </div>
                             )}
                          </div>
                       )}

                       {/* USER */}
                       {msg.role === 'user' && (
                          <div className="flex flex-col items-end">
                              <div className="bg-[#1a1a1a] border border-[#222] text-[#e0e0e0] px-3 py-2 rounded-lg shadow-sm max-w-xl text-[13px]">
                                 {msg.content}
                              </div>
                          </div>
                       )}
                    </div>
                 ))}
                 <div ref={messagesEndRef} className="h-4" />
              </div>
           </div>

           {/* INPUT AREA - Terminal Style */}
           <div className="p-4 bg-gradient-to-t from-black via-black to-transparent z-30">
              <div className="max-w-3xl mx-auto">
                 <div className="relative flex items-start gap-2 p-2.5 bg-[#0a0a0a] border border-[#222] rounded-lg shadow-2xl focus-within:border-[#d97757]/50 focus-within:bg-[#0c0c0c] transition-all group">
                    <div className="mt-1.5 text-[#d97757] animate-pulse">
                        <Terminal className="w-3.5 h-3.5" />
                    </div>
                    <textarea
                       value={input}
                       onChange={(e) => setInput(e.target.value)}
                       onKeyDown={(e) => {
                           if (e.key === 'Enter' && !e.shiftKey) {
                               e.preventDefault();
                               handleSendMessage();
                           }
                       }}
                       placeholder="Describe your task or enter a command..."
                       className="w-full bg-transparent text-[#e0e0e0] text-[13px] font-mono placeholder-[#444] focus:outline-none resize-none py-1 custom-scrollbar"
                       rows={1}
                       style={{ minHeight: '24px', maxHeight: '120px' }}
                       autoFocus
                    />
                    <div className="absolute right-2 bottom-2">
                        <button 
                            onClick={handleSendMessage}
                            disabled={!input.trim()}
                            className={`p-1 rounded transition-all ${input.trim() ? 'bg-[#d97757] text-white shadow-lg shadow-[#d97757]/20' : 'bg-[#1a1a1a] text-[#444]'}`}
                        >
                            <ArrowUp className="w-3 h-3" />
                        </button>
                    </div>
                 </div>
                 <div className="flex justify-center mt-2 gap-4 text-[10px] text-[#444] font-mono">
                     <span className="flex items-center gap-1 hover:text-[#666] cursor-pointer"><Command className="w-3 h-3" /> Actions</span>
                     <span className="flex items-center gap-1 hover:text-[#666] cursor-pointer"><ArrowUp className="w-3 h-3" /> History</span>
                 </div>
              </div>
           </div>

           {/* STATUS LINE */}
           <div className="h-7 bg-[#050505] border-t border-[#1a1a1a] flex items-center justify-between px-3 select-none text-[10px] font-mono text-[#666]">
               <div className="flex items-center gap-4">
                   <div className="flex items-center gap-1.5 hover:text-[#e0e0e0] cursor-pointer transition-colors">
                       <div className={`w-1.5 h-1.5 rounded-full ${isTyping ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'}`}></div>
                       <span>{isTyping ? 'BUSY' : 'READY'}</span>
                   </div>
                   <div className="h-3 w-[1px] bg-[#222]"></div>
                   <div className="flex items-center gap-1.5">
                       <Activity className="w-3 h-3 text-blue-500" />
                       <span>{context}% ctx</span>
                   </div>
               </div>
               
               <div className="flex items-center gap-4">
                   <span>UTF-8</span>
                   <span>TypeScript</span>
                   <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> 00:04:12</span>
               </div>
           </div>
        </main>
      </div>
      <style>{`
        @keyframes fade-in { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fade-in { animation: fade-in 0.3s ease-out forwards; }
        .custom-scrollbar::-webkit-scrollbar { width: 5px; height: 5px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #222; border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #333; }
      `}</style>
    </div>
  );
};

export default App;