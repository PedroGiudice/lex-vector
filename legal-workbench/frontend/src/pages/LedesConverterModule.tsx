import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLedesConverterStore } from '@/store/ledesConverterStore';

// --- Tauri global type ---
declare global {
  interface Window {
    __TAURI__?: Record<string, unknown>;
  }
}

// --- Custom Brutalist Icons ---
const Icons = {
  File: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path
        d="M14 2H6C5.44772 2 5 2.44772 5 3V21C5 21.5523 5.44772 22 6 22H18C18.5523 22 19 21.5523 19 21V8L14 2Z"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="square"
      />
      <path d="M14 2V8H19" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
    </svg>
  ),
  Upload: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path
        d="M12 3L12 15M12 3L8 7M12 3L16 7"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="square"
      />
      <path d="M4 17V21H20V17" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
    </svg>
  ),
  Download: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path
        d="M12 3V15M12 15L8 11M12 15L16 11"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="square"
      />
      <path d="M4 19H20" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
    </svg>
  ),
  Settings: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <rect
        x="2"
        y="6"
        width="20"
        height="2"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="square"
      />
      <rect
        x="2"
        y="16"
        width="20"
        height="2"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="square"
      />
      <rect x="6" y="4" width="4" height="6" fill="currentColor" />
      <rect x="14" y="14" width="4" height="6" fill="currentColor" />
    </svg>
  ),
  Check: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path
        d="M4 12L9 17L20 6"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="square"
        strokeLinejoin="miter"
      />
    </svg>
  ),
  Alert: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path
        d="M12 2L2 22H22L12 2Z"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinejoin="miter"
      />
      <path d="M12 16V17" stroke="currentColor" strokeWidth="3" strokeLinecap="square" />
      <path d="M12 8V13" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
    </svg>
  ),
  Trash: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path d="M3 6H21" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
      <path d="M19 6V21H5V6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
      <rect
        x="9"
        y="3"
        width="6"
        height="3"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="square"
      />
      <path d="M10 10V17" stroke="currentColor" strokeWidth="2" strokeLinecap="square" />
      <path d="M14 10V17" stroke="currentColor" strokeWidth="2" strokeLinecap="square" />
    </svg>
  ),
  Terminal: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path
        d="M4 17L10 11L4 5"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="square"
        strokeLinejoin="miter"
      />
      <path d="M12 19H20" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
    </svg>
  ),
  Briefcase: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <rect
        x="2"
        y="7"
        width="20"
        height="14"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="square"
      />
      <path d="M8 7V4H16V7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
      <path d="M2 11H22" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
  Database: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path
        d="M21 5C21 6.65685 16.9706 8 12 8C7.02944 8 3 6.65685 3 5C3 3.34315 7.02944 2 12 2C16.9706 2 21 3.34315 21 5Z"
        stroke="currentColor"
        strokeWidth="2"
      />
      <path
        d="M21 12C21 13.6569 16.9706 15 12 15C7.02944 15 3 13.6569 3 12"
        stroke="currentColor"
        strokeWidth="2"
      />
      <path
        d="M3 5V19C3 20.6569 7.02944 22 12 22C16.9706 22 21 20.6569 21 19V5"
        stroke="currentColor"
        strokeWidth="2"
      />
    </svg>
  ),
  Hash: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path d="M4 9H20" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
      <path d="M4 15H20" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
      <path d="M10 3L8 21" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
      <path d="M16 3L14 21" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
    </svg>
  ),
  Calendar: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <rect
        x="3"
        y="4"
        width="18"
        height="18"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="square"
      />
      <path d="M16 2V6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
      <path d="M8 2V6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
      <path d="M3 10H21" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
    </svg>
  ),
  Money: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path d="M12 1V23" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
      <path
        d="M17 5H9.5C8.57174 5 7.6815 5.36875 7.02513 6.02513C6.36875 6.6815 6 7.57174 6 8.5C6 9.42826 6.36875 10.3185 7.02513 10.9749C7.6815 11.6313 8.57174 12 9.5 12H14.5C15.4283 12 16.3185 12.3688 16.9749 13.0251C17.6313 13.6815 18 14.5717 18 15.5C18 16.4283 17.6313 17.3185 16.9749 17.9749C16.3185 18.6313 15.4283 19 14.5 19H6"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="square"
      />
    </svg>
  ),
  Save: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path
        d="M19 21H5C4.44772 21 4 20.5523 4 20V4C4 3.44772 4.44772 3 5 3H19C19.5523 3 20 3.44772 20 4V20C20 20.5523 19.5523 21 19 21Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="square"
      />
      <path d="M17 21V13H7V21" stroke="currentColor" strokeWidth="2" strokeLinecap="square" />
      <path d="M7 3V8H15" stroke="currentColor" strokeWidth="2" strokeLinecap="square" />
    </svg>
  ),
  Code: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path d="M16 18L22 12L16 6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
      <path d="M8 6L2 12L8 18" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
    </svg>
  ),
  CaretDown: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path d="M6 9L12 15L18 9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
    </svg>
  ),
  CaretUp: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <path d="M18 15L12 9L6 15" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" />
    </svg>
  ),
  Logo: ({ className, size = 24 }: { className?: string; size?: number }) => (
    <svg viewBox="0 0 24 24" fill="none" width={size} height={size} className={className}>
      <rect
        x="2"
        y="2"
        width="20"
        height="20"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="square"
      />
      <rect x="7" y="7" width="10" height="10" fill="currentColor" />
    </svg>
  ),
};

// --- Google Fonts ---
const FONT_IMPORT = `
  @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
`;

// --- UI Components ---

const Button = ({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  icon: Icon,
  className = '',
}: {
  children?: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  disabled?: boolean;
  icon?: typeof Icons.Upload;
  className?: string;
}) => {
  const baseClasses =
    "flex items-center justify-center gap-2 px-5 py-3 rounded font-bold transition-all duration-150 active:translate-y-0.5 disabled:opacity-50 disabled:pointer-events-none text-xs tracking-wider uppercase font-['Manrope'] border";

  const variants = {
    primary:
      'bg-teal-500 hover:bg-teal-400 text-black border-teal-600 shadow-[2px_2px_0px_0px_rgba(20,184,166,0.3)]',
    secondary: 'bg-[#18181b] hover:bg-[#27272a] text-zinc-300 border-zinc-700',
    danger: 'bg-rose-950/30 hover:bg-rose-900/40 text-rose-400 border-rose-900',
    ghost: 'bg-transparent hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 border-transparent',
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variants[variant]} ${className}`}
    >
      {Icon && <Icon size={14} className={variant === 'primary' ? 'text-black' : 'currentColor'} />}
      {children}
    </button>
  );
};

const DataCard = ({
  label,
  value,
  icon: Icon,
  highlight = false,
}: {
  label: string;
  value: string;
  icon: typeof Icons.File;
  highlight?: boolean;
}) => (
  <div
    className={`flex flex-col p-6 rounded-sm border transition-all duration-300 h-full justify-between ${highlight ? 'bg-teal-950/20 border-teal-500/40' : 'bg-[#121214] border-zinc-800 hover:border-zinc-700'}`}
  >
    <div className="flex items-center gap-2 mb-4 text-zinc-500">
      <Icon size={14} className={highlight ? 'text-teal-400' : 'text-zinc-600'} />
      <span className="text-[10px] font-bold uppercase tracking-widest font-['Manrope']">
        {label}
      </span>
    </div>
    <div
      className={`text-xl font-bold font-['JetBrains_Mono'] tracking-tight truncate ${value ? (highlight ? 'text-teal-300' : 'text-zinc-100') : 'text-zinc-600'}`}
    >
      {value || '---'}
    </div>
  </div>
);

// --- Main Application ---

export default function LedesConverterModule() {
  const [isLogExpanded, setIsLogExpanded] = useState(false);
  const [logs, setLogs] = useState<string[]>(['System ready.']);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Zustand store
  const {
    activeTab,
    setActiveTab,
    file,
    setFile,
    textInput,
    setTextInput,
    matters,
    selectedMatter,
    selectMatter,
    mattersLoading,
    loadMatters,
    status,
    ledesContent,
    extractedData,
    validationIssues,
    error,
    convertFile,
    convertText,
    reset,
  } = useLedesConverterStore();

  // Load matters on mount
  useEffect(() => {
    loadMatters();
  }, [loadMatters]);

  // Auto-scroll logs
  useEffect(() => {
    if (isLogExpanded && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isLogExpanded]);

  const addLog = useCallback((msg: string) => {
    const time = new Date().toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    setLogs((prev) => [...prev, `${time} | ${msg}`]);
  }, []);

  // --- Handlers ---

  const handleFileUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = e.target.files?.[0];
      if (selected) {
        if (
          selected.name.endsWith('.docx') ||
          selected.type ===
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ) {
          setFile(selected);
          addLog(`File: ${selected.name}`);
        } else {
          addLog('ERROR: Invalid file type. Required: .docx');
        }
      }
    },
    [setFile, addLog]
  );

  const handleFileOpen = useCallback(async () => {
    // Try Tauri native file dialog
    if (window.__TAURI__) {
      try {
        const { open } = await import('@tauri-apps/plugin-dialog');
        const { readFile } = await import('@tauri-apps/plugin-fs');
        const selected = await open({
          multiple: false,
          filters: [{ name: 'Word Document', extensions: ['docx'] }],
        });
        if (selected && typeof selected === 'string') {
          const contents = await readFile(selected);
          const fileName =
            selected.split('/').pop() || selected.split('\\').pop() || 'document.docx';
          const newFile = new File([contents], fileName, {
            type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          });
          setFile(newFile);
          addLog(`File: ${fileName}`);
          return;
        }
      } catch (err) {
        console.error('Tauri dialog failed, using web fallback:', err);
      }
    }

    // Web fallback: trigger hidden input
    fileInputRef.current?.click();
  }, [setFile, addLog]);

  const handleConvertDocx = useCallback(async () => {
    if (!file) return;
    addLog('Starting DOCX conversion...');
    await convertFile();
    const state = useLedesConverterStore.getState();
    if (state.status === 'success') {
      addLog('Conversion successful.');
    } else if (state.status === 'error') {
      addLog(`ERROR: ${state.error || 'Conversion failed'}`);
    }
  }, [file, convertFile, addLog]);

  const handleConvertText = useCallback(async () => {
    if (!textInput.trim()) return;
    addLog('Starting text conversion...');
    await convertText();
    const state = useLedesConverterStore.getState();
    if (state.status === 'success') {
      addLog('Text conversion successful.');
    } else if (state.status === 'error') {
      addLog(`ERROR: ${state.error || 'Text conversion failed'}`);
    }
  }, [textInput, convertText, addLog]);

  const handleSave = useCallback(async () => {
    if (!ledesContent) return;
    addLog('Saving LEDES file...');

    const fileName = `${extractedData?.invoice_number || 'LEDES'}_output.txt`;

    // Try Tauri native save dialog
    if (window.__TAURI__) {
      try {
        const { save } = await import('@tauri-apps/plugin-dialog');
        const { writeTextFile } = await import('@tauri-apps/plugin-fs');
        const path = await save({
          defaultPath: fileName,
          filters: [{ name: 'LEDES', extensions: ['txt', 'ledes'] }],
        });
        if (path) {
          await writeTextFile(path, ledesContent);
          addLog(`Saved: ${path}`);
          return;
        }
      } catch (err) {
        console.error('Tauri save failed, using web fallback:', err);
      }
    }

    // Web fallback
    const blob = new Blob([ledesContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();
    URL.revokeObjectURL(url);
    addLog('Download initiated.');
  }, [ledesContent, extractedData, addLog]);

  const isProcessing = status === 'uploading' || status === 'processing' || status === 'validating';

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-300 font-['Manrope'] selection:bg-teal-500/30 selection:text-teal-100 overflow-hidden flex flex-col relative">
      <style>{FONT_IMPORT}</style>

      {/* Background Grid */}
      <div
        className="fixed inset-0 z-0 pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(rgba(113, 113, 122, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(113, 113, 122, 0.1) 1px, transparent 1px)',
          backgroundSize: '20px 20px',
        }}
      ></div>

      {/* Top Navigation */}
      <header className="h-14 border-b border-zinc-800 bg-zinc-950/95 backdrop-blur-sm flex items-center justify-between px-6 shrink-0 z-20">
        <div className="flex items-center gap-3">
          <div className="text-teal-500">
            <Icons.Logo size={28} />
          </div>
          <div>
            <h1 className="text-sm font-extrabold tracking-tight text-zinc-100 leading-none font-['Manrope']">
              LEDES <span className="text-zinc-500">CONVERTER</span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div
            className={`flex items-center gap-2 px-3 py-1 border rounded-sm transition-colors ${isProcessing ? 'bg-lime-900/20 border-lime-800' : 'bg-zinc-900 border-zinc-800'}`}
          >
            <div
              className={`w-2 h-2 ${isProcessing ? 'bg-lime-400 animate-pulse' : 'bg-zinc-600'}`}
            ></div>
            <span
              className={`font-bold uppercase tracking-wider ${isProcessing ? 'text-lime-400' : 'text-zinc-500'}`}
            >
              {isProcessing ? 'PROCESSING' : 'IDLE'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 flex overflow-hidden z-10">
        {/* Left Panel: Workspace */}
        <div className="flex-1 flex flex-col h-full overflow-hidden relative">
          <div className="flex-1 overflow-y-auto p-8 lg:p-12 space-y-12 scroll-smooth">
            {/* Tab Bar */}
            <div className="max-w-6xl mx-auto w-full">
              <div className="flex gap-1 mb-8 border-b border-zinc-800">
                {(['upload', 'text'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-6 py-3 text-xs font-bold uppercase tracking-wider transition-all border-b-2 ${
                      activeTab === tab
                        ? 'text-teal-400 border-teal-500 bg-teal-500/5'
                        : 'text-zinc-500 border-transparent hover:text-zinc-300 hover:border-zinc-700'
                    }`}
                  >
                    {tab === 'upload' ? 'Upload DOCX' : 'Colar Texto'}
                  </button>
                ))}
              </div>
            </div>

            {/* Upload Tab */}
            {activeTab === 'upload' && (
              <section className="max-w-6xl mx-auto w-full">
                <div
                  onClick={handleFileOpen}
                  className={`
                    relative group cursor-pointer transition-all duration-300 ease-out
                    rounded-sm border-2 border-dashed
                    flex items-center gap-8 p-10
                    ${
                      file
                        ? 'border-teal-500 bg-teal-500/5'
                        : 'border-zinc-800 hover:border-zinc-600 bg-[#0e0e10] hover:bg-[#121215]'
                    }
                  `}
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    className="hidden"
                    accept=".docx"
                  />

                  <div
                    className={`
                    w-20 h-20 flex items-center justify-center shrink-0 border-2 transition-colors rounded-sm
                    ${file ? 'bg-teal-500 text-black border-teal-500' : 'bg-zinc-900 text-zinc-600 border-zinc-800 group-hover:border-zinc-600 group-hover:text-zinc-400'}
                  `}
                  >
                    {file ? <Icons.Check size={40} /> : <Icons.Upload size={40} />}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-3">
                      <h3
                        className={`text-xl font-bold uppercase tracking-tight ${file ? 'text-teal-400' : 'text-zinc-200'}`}
                      >
                        {file ? 'Source Acquired' : 'Upload Invoice'}
                      </h3>
                      {!file && (
                        <span className="text-[10px] text-zinc-500 font-bold bg-zinc-900 px-3 py-1.5 rounded-sm border border-zinc-800">
                          .DOCX
                        </span>
                      )}
                    </div>
                    <p className="text-base text-zinc-500 truncate font-mono">
                      {file ? file.name : 'Drag and drop or click to initialize data stream'}
                    </p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-6 mt-8">
                  <Button
                    onClick={handleConvertDocx}
                    disabled={!file || isProcessing}
                    className="flex-1 h-16 text-sm"
                    icon={Icons.Download}
                  >
                    {isProcessing ? 'PROCESSING...' : 'COMPILE & EXPORT'}
                  </Button>
                  {file && (
                    <Button
                      variant="secondary"
                      onClick={() => {
                        reset();
                        setLogs(['System ready.']);
                        addLog('Reset complete.');
                      }}
                      icon={Icons.Trash}
                      className="shrink-0 h-16 w-16"
                    />
                  )}
                </div>

                {error && (
                  <div className="mt-6 p-4 bg-rose-950/20 border-l-4 border-rose-500 text-rose-400 text-sm font-bold flex items-center gap-4">
                    <Icons.Alert size={20} />
                    <span>{error}</span>
                  </div>
                )}
              </section>
            )}

            {/* Text Tab */}
            {activeTab === 'text' && (
              <section className="max-w-6xl mx-auto w-full">
                <div className="relative">
                  <textarea
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder={
                      'Cole aqui o conteudo da fatura...\n\nFormato esperado:\nInvoice # 1234\nDate of Issuance: January 15, 2026\nDraft appeal brief US $1200\nSettlement conference US $800\nTotal Gross Amount: US $2000'
                    }
                    className="w-full h-64 bg-[#121214] border-2 border-zinc-800 hover:border-zinc-700 focus:border-teal-500/50 rounded-sm p-6 text-sm text-zinc-200 font-['JetBrains_Mono'] resize-y outline-none transition-all placeholder:text-zinc-700"
                  />
                  {textInput && (
                    <button
                      onClick={() => setTextInput('')}
                      className="absolute top-3 right-3 text-zinc-600 hover:text-zinc-400 transition-colors"
                    >
                      <Icons.Trash size={16} />
                    </button>
                  )}
                </div>

                <div className="flex items-center gap-6 mt-8">
                  <Button
                    onClick={handleConvertText}
                    disabled={!textInput.trim() || isProcessing}
                    className="flex-1 h-16 text-sm"
                    icon={Icons.Download}
                  >
                    {isProcessing ? 'PROCESSING...' : 'EXTRACT & COMPILE'}
                  </Button>
                </div>

                {error && (
                  <div className="mt-6 p-4 bg-rose-950/20 border-l-4 border-rose-500 text-rose-400 text-sm font-bold flex items-center gap-4">
                    <Icons.Alert size={20} />
                    <span>{error}</span>
                  </div>
                )}
              </section>
            )}

            {/* Preview Section */}
            <section className="max-w-6xl mx-auto w-full pt-10 border-t border-dashed border-zinc-800">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-sm font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-3">
                  <Icons.Hash size={18} />
                  Data Preview
                </h2>
                {status === 'success' && (
                  <Button
                    onClick={handleSave}
                    className="bg-teal-500 hover:bg-teal-400"
                    icon={Icons.Download}
                  >
                    DOWNLOAD LEDES
                  </Button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <DataCard
                  label="Invoice #"
                  value={extractedData?.invoice_number || ''}
                  icon={Icons.File}
                />
                <DataCard
                  label="Date"
                  value={extractedData?.invoice_date || ''}
                  icon={Icons.Calendar}
                />
                <DataCard
                  label="Total"
                  value={
                    extractedData?.invoice_total ? `$${extractedData.invoice_total.toFixed(2)}` : ''
                  }
                  icon={Icons.Money}
                  highlight={!!extractedData}
                />
              </div>

              {/* LEDES Output Preview */}
              <div className="mt-10 bg-[#0c0c0e] border border-zinc-800 rounded-sm overflow-hidden">
                <div className="bg-[#18181b] px-5 py-4 border-b border-zinc-800 flex items-center justify-between">
                  <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
                    LEDES 1998B OUTPUT
                  </span>
                  <div className="flex items-center gap-3">
                    {ledesContent && (
                      <span className="text-[10px] text-zinc-600 font-mono">
                        {ledesContent.split('\n').length} lines
                      </span>
                    )}
                    <Icons.Code size={16} className="text-zinc-600" />
                  </div>
                </div>
                <div className="p-4 font-['JetBrains_Mono'] text-[11px] leading-relaxed max-h-80 overflow-y-auto">
                  {ledesContent ? (
                    ledesContent.split('\n').map((line, idx) => {
                      const lineErrors = validationIssues.filter(
                        (i) => i.line === idx + 1 && i.severity === 'error'
                      );
                      const lineWarnings = validationIssues.filter(
                        (i) => i.line === idx + 1 && i.severity === 'warning'
                      );
                      const hasError = lineErrors.length > 0;
                      const hasWarning = lineWarnings.length > 0;

                      return (
                        <div
                          key={idx}
                          className={`flex gap-3 py-0.5 px-2 rounded-sm ${
                            hasError ? 'bg-rose-950/20' : hasWarning ? 'bg-amber-950/15' : ''
                          }`}
                          title={[...lineErrors, ...lineWarnings].map((i) => i.message).join('; ')}
                        >
                          <span className="text-zinc-700 select-none shrink-0 w-8 text-right">
                            {String(idx + 1).padStart(2, '0')}
                          </span>
                          <span
                            className={`break-all ${
                              hasError
                                ? 'text-rose-400'
                                : hasWarning
                                  ? 'text-amber-400'
                                  : idx === 0
                                    ? 'text-teal-500'
                                    : idx === 1
                                      ? 'text-zinc-500'
                                      : 'text-zinc-400'
                            }`}
                          >
                            {line}
                          </span>
                        </div>
                      );
                    })
                  ) : (
                    <span className="opacity-30 italic font-['Manrope'] text-zinc-600 px-2">
                      // Waiting for conversion...
                    </span>
                  )}
                </div>
              </div>
            </section>
          </div>

          {/* Collapsible Log Console */}
          <div
            className={`shrink-0 bg-zinc-950 border-t border-zinc-800 transition-all duration-300 ease-in-out flex flex-col ${isLogExpanded ? 'h-64' : 'h-10'}`}
          >
            <button
              onClick={() => setIsLogExpanded(!isLogExpanded)}
              className="w-full flex justify-between items-center px-4 h-10 bg-zinc-900/30 hover:bg-zinc-900/60 transition-colors cursor-pointer border-b border-zinc-800/0 hover:border-zinc-800 group"
            >
              <div className="flex items-center gap-3">
                <Icons.Terminal
                  size={14}
                  className={isProcessing ? 'text-lime-500' : 'text-zinc-600'}
                />
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest group-hover:text-zinc-400 transition-colors">
                  System Log
                </span>
                <span className="text-[10px] text-zinc-600 font-mono ml-2 opacity-50 hidden md:inline border-l border-zinc-800 pl-3">
                  {logs[logs.length - 1]?.split('|')[1] || 'Idle'}
                </span>
              </div>
              {isLogExpanded ? (
                <Icons.CaretDown size={14} className="text-zinc-600" />
              ) : (
                <Icons.CaretUp size={14} className="text-zinc-600" />
              )}
            </button>

            <div
              className="flex-1 overflow-y-auto p-5 space-y-1 bg-[#050505]"
              style={{ scrollBehavior: 'smooth' }}
            >
              {logs.map((log, i) => (
                <div key={i} className="text-[11px] text-zinc-500 font-mono flex gap-4">
                  <span className="opacity-30 shrink-0 select-none w-16">{log.split('|')[0]}</span>
                  <span className={i === logs.length - 1 ? 'text-lime-500' : 'text-zinc-400'}>
                    {log.split('|')[1]}
                  </span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>

        {/* Right Panel: Matter Selector */}
        <aside className="w-96 bg-zinc-900 border-l border-zinc-800 flex flex-col h-full z-10 shadow-2xl shrink-0">
          <div className="p-8 border-b border-zinc-800">
            <h2 className="text-sm font-bold text-zinc-200 flex items-center gap-3 uppercase tracking-widest">
              <Icons.Briefcase size={18} className="text-violet-500" />
              Matter
            </h2>
          </div>

          <div className="flex-1 overflow-y-auto p-8 space-y-8">
            {/* Matter Dropdown */}
            <div className="space-y-3">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                Selecionar Matter
              </label>
              <div className="relative">
                <select
                  value={selectedMatter || ''}
                  onChange={(e) => selectMatter(e.target.value || null)}
                  disabled={mattersLoading}
                  className="w-full bg-[#121214] border-2 border-zinc-800 hover:border-zinc-700 focus:border-violet-500 rounded-sm px-4 py-3 text-sm text-zinc-200 font-['Manrope'] font-medium outline-none transition-all appearance-none cursor-pointer"
                >
                  <option value="">-- Sem matter --</option>
                  {matters.map((m) => (
                    <option key={m.matter_name} value={m.matter_name}>
                      {m.matter_name}
                    </option>
                  ))}
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-600">
                  <Icons.CaretDown size={16} />
                </div>
              </div>
              {mattersLoading && (
                <p className="text-[10px] text-zinc-600 font-mono">Carregando matters...</p>
              )}
            </div>

            {/* Selected Matter Info */}
            {selectedMatter &&
              (() => {
                const m = matters.find((mt) => mt.matter_name === selectedMatter);
                if (!m) return null;
                return (
                  <div className="space-y-4 pt-4 border-t border-zinc-800/50">
                    <div className="flex items-center gap-3 pb-2">
                      <Icons.Database size={14} className="text-zinc-600" />
                      <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                        Detalhes
                      </span>
                    </div>
                    {(
                      [
                        ['Matter ID', m.matter_id],
                        ['Client', `${m.client_name || m.client_id}`],
                        ['Firm', `${m.law_firm_name || m.law_firm_id}`],
                        ['Timekeeper', m.timekeeper_name || '--'],
                        ['Rate', m.unit_cost ? `$${m.unit_cost.toFixed(2)}/h` : '--'],
                      ] as const
                    ).map(([label, value]) => (
                      <div key={label} className="flex justify-between items-center">
                        <span className="text-[10px] text-zinc-600 uppercase tracking-wider">
                          {label}
                        </span>
                        <span className="text-xs text-zinc-300 font-['JetBrains_Mono'] truncate ml-4 max-w-[180px]">
                          {value}
                        </span>
                      </div>
                    ))}
                  </div>
                );
              })()}

            {/* Validation Summary */}
            {validationIssues.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-zinc-800/50">
                <div className="flex items-center gap-3 pb-2">
                  <Icons.Alert size={14} className="text-zinc-600" />
                  <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                    Validacao
                  </span>
                </div>
                {(() => {
                  const errors = validationIssues.filter((i) => i.severity === 'error');
                  const warnings = validationIssues.filter((i) => i.severity === 'warning');
                  return (
                    <>
                      {errors.length > 0 && (
                        <div className="flex items-center gap-2 px-3 py-2 bg-rose-950/20 border border-rose-900/50 rounded-sm">
                          <div className="w-2 h-2 bg-rose-500 shrink-0"></div>
                          <span className="text-[10px] font-bold text-rose-400 uppercase">
                            {errors.length} error{errors.length > 1 ? 's' : ''}
                          </span>
                        </div>
                      )}
                      {warnings.length > 0 && (
                        <div className="flex items-center gap-2 px-3 py-2 bg-amber-950/20 border border-amber-900/50 rounded-sm">
                          <div className="w-2 h-2 bg-amber-500 shrink-0"></div>
                          <span className="text-[10px] font-bold text-amber-400 uppercase">
                            {warnings.length} warning{warnings.length > 1 ? 's' : ''}
                          </span>
                        </div>
                      )}
                      {errors.length === 0 && warnings.length === 0 && ledesContent && (
                        <div className="flex items-center gap-2 px-3 py-2 bg-teal-950/20 border border-teal-900/50 rounded-sm">
                          <div className="w-2 h-2 bg-teal-500 shrink-0"></div>
                          <span className="text-[10px] font-bold text-teal-400 uppercase">
                            Valid LEDES
                          </span>
                        </div>
                      )}
                      <div className="space-y-1 max-h-60 overflow-y-auto">
                        {validationIssues.slice(0, 20).map((issue, idx) => (
                          <div
                            key={idx}
                            className={`text-[10px] font-mono px-2 py-1.5 rounded-sm ${
                              issue.severity === 'error'
                                ? 'text-rose-400 bg-rose-950/10'
                                : 'text-amber-400 bg-amber-950/10'
                            }`}
                          >
                            L{issue.line} {issue.field_name}: {issue.message}
                          </div>
                        ))}
                        {validationIssues.length > 20 && (
                          <p className="text-[10px] text-zinc-600">
                            +{validationIssues.length - 20} more...
                          </p>
                        )}
                      </div>
                    </>
                  );
                })()}
              </div>
            )}

            {/* Valid LEDES indicator when no issues but content exists */}
            {validationIssues.length === 0 && ledesContent && (
              <div className="space-y-4 pt-4 border-t border-zinc-800/50">
                <div className="flex items-center gap-3 pb-2">
                  <Icons.Check size={14} className="text-zinc-600" />
                  <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                    Validacao
                  </span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 bg-teal-950/20 border border-teal-900/50 rounded-sm">
                  <div className="w-2 h-2 bg-teal-500 shrink-0"></div>
                  <span className="text-[10px] font-bold text-teal-400 uppercase">Valid LEDES</span>
                </div>
              </div>
            )}
          </div>

          {/* Save Button at bottom */}
          <div className="p-8 border-t border-zinc-800 bg-zinc-900">
            <Button
              variant="secondary"
              onClick={handleSave}
              disabled={!ledesContent}
              className="w-full text-xs h-14 border-zinc-700 hover:border-teal-500 hover:text-teal-400 group"
              icon={Icons.Save}
            >
              SAVE LEDES FILE
            </Button>
          </div>
        </aside>
      </main>
    </div>
  );
}
