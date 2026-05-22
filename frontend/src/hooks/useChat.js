import { useState } from 'react';
import client from '../api/client';
import useChatStore from '../store/chatStore';

function getTokens(usage) {
  if (usage?.total_tokens) return usage.total_tokens;
  const prompt = usage?.prompt_tokens || 0;
  const completion = usage?.completion_tokens || 0;
  return prompt + completion || null;
}

export function useChat() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const store = useChatStore();

  const sendMessage = async (message, conversationId = null) => {
    setLoading(true); setError(null);
    try {
      const res = await client.post('/chat', { conversation_id: conversationId, message, provider: store.provider, stream: false });
      const { conversation_id, message_id, content, provider, model, usage } = res.data;
      const totalTokens = getTokens(usage);

      if (!conversationId) {
        store.setActiveConversation(conversation_id);
        store.addConversation({ id: conversation_id, title: message.slice(0, 40), provider, model, status: 'active', message_count: 2, total_tokens: totalTokens || 0, created_at: new Date().toISOString(), updated_at: new Date().toISOString() });
      }

      store.addMessage(conversation_id, { id: message_id + '_user', role: 'user', content: message, created_at: new Date().toISOString(), sequence_num: Date.now() });
      store.addMessage(conversation_id, { id: message_id, role: 'assistant', content, created_at: new Date().toISOString(), token_count: totalTokens, provider, model: usage?.model || model, sequence_num: Date.now() + 1 });

      return res.data;
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to send message';
      setError(msg); throw err;
    } finally { setLoading(false); }
  };

  return { sendMessage, loading, error };
}
