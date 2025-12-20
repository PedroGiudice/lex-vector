import { Sparkles, User } from 'lucide-react';
import MessageContent from './MessageContent';

export default function MessageBubble({ message, isUser }) {
  return (
    <div className={`flex gap-3 py-4 ${isUser ? 'justify-end' : ''}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-orange-500/10 flex items-center justify-center flex-shrink-0">
          <Sparkles size={16} className="text-orange-500" />
        </div>
      )}

      <div className={`max-w-3xl ${isUser ? 'order-first' : ''}`}>
        <div className="text-xs text-zinc-500 mb-1 uppercase font-medium">
          {isUser ? 'You' : 'Claude'}
        </div>
        <MessageContent content={message.content} />
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center flex-shrink-0">
          <User size={16} className="text-zinc-300" />
        </div>
      )}
    </div>
  );
}
