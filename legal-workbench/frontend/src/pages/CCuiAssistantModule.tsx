import { useState, useCallback, useRef, useEffect } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  CCuiHeader,
  CCuiIconRail,
  CCuiSidebar,
  CCuiStatusBar,
  CCuiChatInput,
  CCuiMessage,
} from '@/components/ccui-assistant';

interface Message {
  id: string | number;
  role: 'user' | 'assistant';
  content: string;
  type?: 'text' | 'thought';
  label?: string;
  duration?: number;
  isStreaming?: boolean;
}

interface Session {
  id: string;
  title: string;
  updatedAt: string;
}

/**
 * Claude Code Module
 *
 * Terminal-style chat interface for Claude Code.
 * Technical Director role for development assistance.
 */
export default function CCuiAssistantModule() {
  const [sidebarView, setSidebarView] = useState('chat');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [contextPercent, setContextPercent] = useState(0);
  const [sessions, setSessions] = useState<Session[]>([
    { id: '1', title: 'Análise de Contrato', updatedAt: new Date().toISOString() },
    { id: '2', title: 'Pesquisa Jurisprudência', updatedAt: new Date(Date.now() - 86400000).toISOString() },
  ]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages]);

  const handleViewChange = useCallback((view: string) => {
    setSidebarView(view);
  }, []);

  const handleSessionSelect = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId);
    // In production, load messages from backend
    setMessages([]);
  }, []);

  const handleNewChat = useCallback(() => {
    setActiveSessionId(null);
    setMessages([]);
  }, []);

  const handleSendMessage = useCallback((content: string) => {
    if (!content.trim()) return;

    // Add user message
    const userMsg: Message = {
      id: Date.now(),
      role: 'user',
      content: content.trim(),
      type: 'text',
    };
    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    // Simulate AI response (replace with real API call)
    setTimeout(() => {
      const assistantMsg: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Entendi sua solicitação sobre "${content.substring(0, 50)}..."\n\nEsta é uma resposta simulada do assistente jurídico. Em produção, aqui seria integrado com o backend de IA para processamento de documentos legais.\n\n\`\`\`python\n# Exemplo de código\ndef analyze_contract(doc):\n    return extract_clauses(doc)\n\`\`\``,
        type: 'text',
      };
      setMessages(prev => [...prev, assistantMsg]);
      setIsProcessing(false);
      setContextPercent(prev => Math.min(prev + 5, 100));
    }, 1500);
  }, []);

  const handleSettingsClick = useCallback(() => {
    console.log('Settings clicked');
  }, []);

  return (
    <div className="flex flex-col h-full w-full bg-ccui-bg-primary text-ccui-text-primary font-mono overflow-hidden">
      {/* Back to Hub Header */}
      <div className="h-10 bg-ccui-bg-secondary border-b border-ccui-border-primary flex items-center px-4">
        <Link
          to="/"
          className="flex items-center gap-2 text-ccui-text-muted hover:text-ccui-accent transition-colors text-sm"
        >
          <ArrowLeft size={14} />
          <span>Voltar ao Hub</span>
        </Link>
        <div className="ml-auto text-xs text-ccui-text-subtle">
          Claude Code - Technical Director
        </div>
      </div>

      {/* CCui Header */}
      <CCuiHeader
        projectPath="~/legal-workbench"
        currentModel="Claude Sonnet"
        onSettingsClick={handleSettingsClick}
      />

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Icon Rail */}
        <CCuiIconRail
          activeView={sidebarView}
          onViewChange={handleViewChange}
          onSettingsClick={handleSettingsClick}
        />

        {/* Sidebar - hidden on mobile */}
        <div className="hidden md:block">
          <CCuiSidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSessionSelect={handleSessionSelect}
            onNewChat={handleNewChat}
          />
        </div>

        {/* Main Content */}
        <main className="flex-1 flex flex-col relative bg-ccui-bg-primary">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 md:p-8 pb-32">
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.length === 0 && (
                <div className="text-center py-20">
                  <div className="text-ccui-accent text-4xl mb-4">🤖</div>
                  <div className="text-ccui-text-muted text-sm mb-2">
                    Claude Code
                  </div>
                  <div className="text-ccui-text-subtle text-xs">
                    Technical Director - descreva sua tarefa
                  </div>
                </div>
              )}
              {messages.map((msg, index) => (
                <CCuiMessage
                  key={msg.id || index}
                  message={msg}
                  isStreaming={msg.isStreaming}
                />
              ))}
              <div ref={messagesEndRef} className="h-4" />
            </div>
          </div>

          {/* Input Area */}
          <CCuiChatInput
            onSend={handleSendMessage}
            disabled={isProcessing}
            placeholder={
              isProcessing
                ? 'Processando...'
                : 'Descreva sua tarefa...'
            }
          />
        </main>
      </div>

      {/* Status Bar */}
      <CCuiStatusBar
        isProcessing={isProcessing}
        contextPercent={contextPercent}
      />
    </div>
  );
}
