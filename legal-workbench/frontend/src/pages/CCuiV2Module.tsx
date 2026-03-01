import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  CCuiLayout,
  WebSocketProvider,
  AuthProvider,
  ChatHistoryProvider,
} from '@/components/ccui-v2';

/**
 * CCui V2 Module
 *
 * Interface de comando juridico para Claude Code via browser.
 * Design: editorial escuro, precisao cirurgica, Instrument Serif + Geist Mono.
 */
export default function CCuiV2Module() {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <ChatHistoryProvider>
          <div
            className="flex flex-col h-full w-full bg-[#0d0a08] overflow-hidden"
            style={{ zoom: 0.85 }}
          >
            {/* Back to Hub */}
            <div className="h-8 bg-[#0d0a08] border-b border-[#231d15] flex items-center px-4 z-50">
              <Link
                to="/"
                className="flex items-center gap-2 text-[#3e3222] hover:text-[#a0603a] transition-colors text-[11px]"
                style={{ fontFamily: "'Geist Mono', monospace" }}
              >
                <ArrowLeft size={12} strokeWidth={1.4} />
                <span className="tracking-wider">VOLTAR</span>
              </Link>
            </div>

            {/* CCui Layout */}
            <div className="flex-1 overflow-hidden">
              <CCuiLayout />
            </div>
          </div>
        </ChatHistoryProvider>
      </WebSocketProvider>
    </AuthProvider>
  );
}
