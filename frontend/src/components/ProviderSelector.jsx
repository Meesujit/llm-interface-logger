import { MessageSquare, Settings } from 'lucide-react';
import useChatStore from '../store/chatStore';

export default function ProviderSelector() {
  const provider = useChatStore((s) => s.provider);
  const setProvider = useChatStore((s) => s.setProvider);

  return (
    <div className="flex items-center gap-1">
      <button onClick={() => setProvider('groq')}
        className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${provider === 'groq' ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/30' : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'}`}>
        <MessageSquare className="w-3.5 h-3.5 inline mr-1" />Groq</button>
      <button onClick={() => setProvider('gemini')}
        className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${provider === 'gemini' ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30' : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'}`}>
        <Settings className="w-3.5 h-3.5 inline mr-1" />Gemini</button>
    </div>
  );
}
