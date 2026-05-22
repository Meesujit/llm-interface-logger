import { useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import MessageBubble from './MessageBubble';
import StreamingIndicator from './StreamingIndicator';
import useChatStore from '../store/chatStore';

export default function ChatWindow({ messages, onSend, loading }) {
  const scrollRef = useRef(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const streamingContent = useChatStore((s) => s.streamingContent);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, streamingContent]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const text = inputRef.current.value.trim();
    if (!text || loading || isStreaming) return;
    onSend(text); inputRef.current.value = '';
  };

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e); } };

  return (
    <div className="flex flex-col h-full">
      <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto">
        <div className="max-w-3xl mx-auto w-full">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
              <div className="w-16 h-16 rounded-2xl bg-gray-800 flex items-center justify-center mb-6">
                <Send className="w-8 h-8 text-gray-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-300 mb-2">LLM Inference Logger</h2>
              <p className="text-sm text-gray-600 max-w-md">Chat with Groq or Gemini. Every inference is logged with latency, token usage, and PII redaction.</p>
            </div>
          )}

          {messages.map((msg) => (<MessageBubble key={msg.id || msg.sequence_num} message={msg} />))}

          {isStreaming && streamingContent && (
            <div className="flex gap-4 px-6 py-3">
              <div className="w-7 h-7 rounded-full bg-primary-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs text-primary-400">*</span>
              </div>
              <div className="max-w-[85%] rounded-2xl px-4 py-2.5 bg-gray-800 text-gray-100">
                <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">{streamingContent}
                  <span className="inline-block w-1.5 h-4 bg-primary-400 ml-0.5 animate-pulse rounded-sm align-middle" />
                </p>
              </div>
            </div>
          )}
          {isStreaming && <StreamingIndicator />}
          {loading && !isStreaming && (
            <div className="flex gap-4 px-6 py-3">
              <div className="w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center flex-shrink-0 mt-0.5"><span className="text-xs text-gray-500">*</span></div>
              <div className="bg-gray-800 rounded-2xl px-4 py-3">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} className="h-4" />
        </div>
      </div>

      <div className="flex-shrink-0 border-t border-gray-800 bg-gray-900 p-3">
        <div className="max-w-3xl mx-auto w-full">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input ref={inputRef} type="text" onKeyDown={handleKeyDown} placeholder="Send a message..."
              className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
              disabled={loading || isStreaming} autoFocus />
            <button type="submit" disabled={loading || isStreaming}
              className="bg-primary-600 hover:bg-primary-500 disabled:bg-gray-800 disabled:text-gray-600 text-white rounded-xl px-3 py-2.5 transition-colors">
              <Send className="w-4 h-4" />
            </button>
          </form>
          <p className="text-[10px] text-gray-600 text-center mt-1.5">LLM Inference Logger</p>
        </div>
      </div>
    </div>
  );
}
