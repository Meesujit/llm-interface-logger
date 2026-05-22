import { useCallback, useRef } from 'react';
import useChatStore from '../store/chatStore';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useStream() {
  const store = useChatStore();
  const eventSourceRef = useRef(null);

  const startStream = useCallback(async (message, conversationId, provider, model) => {
    store.setStreaming(true); store.clearStreaming();
    const params = new URLSearchParams({ conversation_id: conversationId, message, provider, ...(model && { model }) });
    const url = `${API_BASE}/api/chat/stream?${params.toString()}`;
    const controller = new AbortController();
    eventSourceRef.current = controller;

    try {
      const response = await fetch(url, { headers: { Accept: 'text/event-stream' }, signal: controller.signal });
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.chunk) store.appendStreamChunk(data.chunk);
              if (data.done) {
                store.addMessage(conversationId, { id: Date.now().toString(), role: 'assistant', content: store.streamingContent, created_at: new Date().toISOString(), token_count: data.usage?.total_tokens || 0, sequence_num: Date.now() });
                store.clearStreaming(); return;
              }
            } catch (e) {}
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') { store.setStreaming(false); store.clearStreaming(); }
    }
  }, [store]);

  const stopStream = useCallback(() => {
    if (eventSourceRef.current) { eventSourceRef.current.abort(); eventSourceRef.current = null; }
    store.setStreaming(false); store.clearStreaming();
  }, [store]);

  return { startStream, stopStream };
}
