import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { CCuiLayout, WebSocketProvider, AuthProvider } from '@/components/ccui-v2';

/**
 * CCui V2 Module
 *
 * Terminal-style chat interface for Claude Code with animated spinners.
 * New UI based on the CCUI-SPINNER design system.
 */
export default function CCuiV2Module() {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <div className="flex flex-col h-full w-full bg-[#000000] overflow-hidden">
          {/* Back to Hub Header */}
          <div className="h-10 bg-[#050505] border-b border-[#27272a] flex items-center px-4 z-50">
            <Link
              to="/"
              className="flex items-center gap-2 text-[#b5b5b5] hover:text-[#d97757] transition-colors text-sm"
            >
              <ArrowLeft size={14} />
              <span>Voltar ao Hub</span>
            </Link>
            <div className="ml-auto text-xs text-[#666]">
              Claude Code CLI v2
            </div>
          </div>

          {/* CCui Layout */}
          <div className="flex-1 overflow-hidden">
            <CCuiLayout />
          </div>
        </div>
      </WebSocketProvider>
    </AuthProvider>
  );
}
