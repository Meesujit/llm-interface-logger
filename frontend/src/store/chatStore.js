import { create } from 'zustand';

const useChatStore = create((set, get) => ({
  conversations: [], folders: [], activeConversationId: null, activeFolderId: null,
  messages: {}, isStreaming: false, streamingContent: '', provider: 'groq',

  setProvider: (p) => set({ provider: p }),
  setConversations: (c) => set({ conversations: c }),
  setFolders: (f) => set({ folders: f }),
  setActiveConversation: (id) => set({ activeConversationId: id }),
  setActiveFolder: (id) => set({ activeFolderId: id }),
  addConversation: (c) => set((s) => ({ conversations: [c, ...s.conversations] })),
  updateConversation: (id, u) => set((s) => ({ conversations: s.conversations.map(c => c.id === id ? { ...c, ...u } : c) })),
  removeConversation: (id) => set((s) => ({ conversations: s.conversations.filter(c => c.id !== id), activeConversationId: s.activeConversationId === id ? null : s.activeConversationId })),
  cancelConversation: (id) => set((s) => ({ conversations: s.conversations.map(c => c.id === id ? { ...c, status: 'cancelled' } : c) })),
  resumeConversation: (id) => set((s) => ({ conversations: s.conversations.map(c => c.id === id ? { ...c, status: 'active' } : c) })),
  addFolder: (f) => set((s) => ({ folders: [...s.folders, f] })),
  updateFolder: (id, u) => set((s) => ({ folders: s.folders.map(f => f.id === id ? { ...f, ...u } : f) })),
  removeFolder: (id) => set((s) => ({ folders: s.folders.filter(f => f.id !== id), activeFolderId: s.activeFolderId === id ? null : s.activeFolderId })),
  setMessages: (cid, msgs) => set((s) => ({ messages: { ...s.messages, [cid]: msgs } })),
  addMessage: (cid, msg) => set((s) => ({ messages: { ...s.messages, [cid]: [...(s.messages[cid] || []), msg] } })),
  setStreaming: (b) => set({ isStreaming: b }),
  appendStreamChunk: (chunk) => set((s) => ({ streamingContent: s.streamingContent + chunk })),
  clearStreaming: () => set({ streamingContent: '', isStreaming: false }),
}));

export default useChatStore;
