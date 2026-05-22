import { useState } from 'react';
import ConversationList from '../components/ConversationList';
import ChatWindow from '../components/ChatWindow';
import ProviderSelector from '../components/ProviderSelector';
import useChatStore from '../store/chatStore';
import { useChat } from '../hooks/useChat';
import { useConversations } from '../hooks/useConversations';
import { useStream } from '../hooks/useStream';
import { MessageSquare, Activity, PanelLeftClose, PanelLeft, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function ChatPage() {
  const navigate = useNavigate();
  const store = useChatStore();
  const { sendMessage, loading } = useChat();
  const { fetchMessages, renameConversation, moveConversation, cancelConversation, resumeConversation, createFolder, renameFolder, deleteFolder } = useConversations();
  const { startStream } = useStream();
  const [streamEnabled, setStreamEnabled] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const activeMessages = store.activeConversationId ? store.messages[store.activeConversationId] || [] : [];

  const handleSelectConversation = async (convId) => { store.setActiveConversation(convId); if (convId) await fetchMessages(convId); };
  const handleNewChat = () => store.setActiveConversation(null);
  const handleCancel = async (convId) => { await cancelConversation(convId); if (store.activeConversationId === convId) store.setActiveConversation(null); };

  const handleSend = async (message) => {
    const convId = store.activeConversationId;
    if (streamEnabled && convId) {
      store.addMessage(convId, { id: Date.now().toString(), role: 'user', content: message, created_at: new Date().toISOString(), sequence_num: Date.now() });
      await startStream(message, convId, store.provider); return;
    }
    try {
      const result = await sendMessage(message, convId);
      if (!store.activeConversationId) store.setActiveConversation(result.conversation_id);
    } catch (err) {}
  };

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950">
      <aside className={`${sidebarOpen ? 'w-64' : 'w-0'} flex-shrink-0 border-r border-gray-800 bg-gray-900 transition-all duration-200 overflow-hidden`}>
        <div className="flex flex-col h-full w-64">
          <div className="flex-shrink-0 p-3 border-b border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <h1 className="text-sm font-bold text-white flex items-center gap-2"><MessageSquare className="w-4 h-4 text-primary-400" />LLM Logger</h1>
              <div className="flex items-center gap-1">
                <button onClick={() => navigate('/dashboard')} className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"><Activity className="w-3.5 h-3.5" /></button>
                <button onClick={() => setSidebarOpen(false)} className="p-1.5 rounded-lg hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition-colors"><PanelLeftClose className="w-3.5 h-3.5" /></button>
              </div>
            </div>
            <button onClick={handleNewChat} className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg px-3 py-2 text-xs font-medium transition-colors"><Plus className="w-3.5 h-3.5" />New Chat</button>
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
            <ConversationList onSelect={handleSelectConversation} onCancel={handleCancel} onResume={resumeConversation} onRename={renameConversation} onMove={moveConversation} onCreateFolder={createFolder} onRenameFolder={renameFolder} onDeleteFolder={deleteFolder} />
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="flex-shrink-0 h-12 border-b border-gray-800 bg-gray-900 flex items-center justify-between px-4">
          <div className="flex items-center gap-3">
            {!sidebarOpen && <button onClick={() => setSidebarOpen(true)} className="p-1.5 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"><PanelLeft className="w-4 h-4" /></button>}
            <h2 className="text-sm font-medium text-gray-300 truncate">{store.activeConversationId ? 'Chat' : 'New Conversation'}</h2>
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1.5 text-xs text-gray-500 cursor-pointer select-none"><input type="checkbox" checked={streamEnabled} onChange={(e) => setStreamEnabled(e.target.checked)} className="rounded bg-gray-700 border-gray-600 text-primary-500 focus:ring-primary-500" />Stream</label>
            <ProviderSelector />
          </div>
        </header>
        <div className="flex-1 min-h-0"><ChatWindow messages={activeMessages} onSend={handleSend} loading={loading} /></div>
      </div>
    </div>
  );
}
