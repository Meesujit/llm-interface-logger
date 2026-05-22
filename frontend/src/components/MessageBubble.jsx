import { User, Bot, Cpu } from 'lucide-react';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const tokenCount = message.token_count;
  const isLoading = tokenCount === null || tokenCount === undefined;

  return (
    <div className={`flex gap-4 px-6 py-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-primary-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Bot className="w-3.5 h-3.5 text-primary-400" />
        </div>
      )}
      <div className="max-w-[75%]">
        <div className={`rounded-2xl px-4 py-2.5 ${isUser ? 'bg-primary-600 text-white rounded-br-md' : 'bg-gray-800 text-gray-100 rounded-bl-md'}`}>
          <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">{message.content}</p>
        </div>
        {!isUser && (
          <div className="mt-1 px-1">
            {isLoading ? (
              <span className="inline-flex items-center gap-1.5 text-[10px] text-gray-600">
                <span className="w-1.5 h-1.5 bg-gray-700 rounded-full animate-pulse" />
                <span className="w-1.5 h-1.5 bg-gray-700 rounded-full animate-pulse" style={{ animationDelay: '200ms' }} />
                <span className="w-1.5 h-1.5 bg-gray-700 rounded-full animate-pulse" style={{ animationDelay: '400ms' }} />
              </span>
            ) : tokenCount > 0 ? (
              <span className="inline-flex items-center gap-1 text-[10px] text-gray-500">
                <Cpu className="w-3 h-3" />{tokenCount.toLocaleString()} tokens
                {message.model && <span className="text-gray-600 ml-1">{message.model.split('-')[0]}</span>}
              </span>
            ) : null}
          </div>
        )}
      </div>
      {isUser && (
        <div className="w-7 h-7 rounded-full bg-orange-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
          <User className="w-3.5 h-3.5 text-orange-400" />
        </div>
      )}
    </div>
  );
}
