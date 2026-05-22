import { useState, useRef, useEffect } from 'react';
import { FolderOpen, FolderPlus, ChevronDown, ChevronRight, MoreHorizontal, Pencil, Trash2, FolderInput, Check, X } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import useChatStore from '../store/chatStore';

export default function ConversationList({ onSelect, onCancel, onResume, onRename, onMove, onCreateFolder, onRenameFolder, onDeleteFolder }) {
  const conversations = useChatStore((s) => s.conversations);
  const folders = useChatStore((s) => s.folders);
  const activeId = useChatStore((s) => s.activeConversationId);
  const activeFolderId = useChatStore((s) => s.activeFolderId);
  const setActiveFolder = useChatStore((s) => s.setActiveFolder);

  const [collapsedFolders, setCollapsedFolders] = useState({});
  const [editingConvId, setEditingConvId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [menuConvId, setMenuConvId] = useState(null);
  const [creatingFolder, setCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [editingFolderId, setEditingFolderId] = useState(null);
  const [editFolderName, setEditFolderName] = useState('');
  const menuRef = useRef(null);
  const editInputRef = useRef(null);

  useEffect(() => {
    const handler = (e) => { if (menuRef.current && !menuRef.current.contains(e.target)) setMenuConvId(null); };
    document.addEventListener('mousedown', handler); return () => document.removeEventListener('mousedown', handler);
  }, []);
  useEffect(() => { if (editingConvId && editInputRef.current) { editInputRef.current.focus(); editInputRef.current.select(); } }, [editingConvId]);

  const toggleFolder = (id) => setCollapsedFolders((p) => ({ ...p, [id]: !p[id] }));
  const startRename = (conv) => { setEditingConvId(conv.id); setEditTitle(conv.title || 'Untitled'); setMenuConvId(null); };
  const submitRename = async () => { if (editingConvId && editTitle.trim()) await onRename(editingConvId, editTitle.trim()); setEditingConvId(null); };
  const handleRenameKeyDown = (e) => { if (e.key === 'Enter') submitRename(); if (e.key === 'Escape') setEditingConvId(null); };
  const handleCreateFolder = async () => { if (newFolderName.trim()) { await onCreateFolder(newFolderName.trim()); setNewFolderName(''); setCreatingFolder(false); } };
  const startRenameFolder = (folder) => { setEditingFolderId(folder.id); setEditFolderName(folder.name); };
  const submitRenameFolder = async () => { if (editingFolderId && editFolderName.trim()) await onRenameFolder(editingFolderId, editFolderName.trim()); setEditingFolderId(null); };

  const folderConvCounts = {};
  conversations.forEach((c) => { if (c.folder_id && c.status === 'active') folderConvCounts[c.folder_id] = (folderConvCounts[c.folder_id] || 0) + 1; });

  const filteredConvs = conversations.filter((c) => c.status === 'active' && (activeFolderId ? c.folder_id === activeFolderId : !c.folder_id));

  const pc = { groq: 'bg-orange-500/30 text-orange-400', gemini: 'bg-blue-500/30 text-blue-400' };

  const renderConv = (conv) => (
    <div key={conv.id} onClick={() => editingConvId !== conv.id && onSelect(conv.id)}
      className={`group relative px-2 py-2 mx-1 rounded-lg cursor-pointer transition-colors ${activeId === conv.id ? 'bg-gray-800' : 'hover:bg-gray-800/40'}`}>
      {editingConvId === conv.id ? (
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <input ref={editInputRef} value={editTitle} onChange={(e) => setEditTitle(e.target.value)} onKeyDown={handleRenameKeyDown} onBlur={submitRename}
            className="flex-1 bg-gray-700 border border-gray-600 rounded px-2 py-0.5 text-xs text-white focus:outline-none focus:border-primary-500" />
          <button onClick={submitRename} className="p-0.5 text-green-400 hover:text-green-300"><Check className="w-3.5 h-3.5" /></button>
          <button onClick={() => setEditingConvId(null)} className="p-0.5 text-gray-500 hover:text-gray-300"><X className="w-3.5 h-3.5" /></button>
        </div>
      ) : (
        <>
          <p className="text-xs text-gray-300 truncate pr-6 leading-relaxed">{conv.title || 'New Chat'}</p>
          <div className="flex items-center gap-1.5 mt-1">
            <span className="text-[10px] text-gray-600">{conv.created_at ? formatDistanceToNow(new Date(conv.created_at), { addSuffix: true }) : ''}</span>
            <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium ${pc[conv.provider] || 'bg-gray-700 text-gray-500'}`}>{conv.provider}</span>
          </div>
          <button onClick={(e) => { e.stopPropagation(); setMenuConvId(menuConvId === conv.id ? null : conv.id); }}
            className="absolute top-1.5 right-1 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-700 text-gray-500 hover:text-gray-200 transition-all">
            <MoreHorizontal className="w-3.5 h-3.5" /></button>
          {menuConvId === conv.id && (
            <div ref={menuRef} className="absolute right-0 top-8 z-20 bg-gray-800 border border-gray-700 rounded-lg shadow-xl py-1 min-w-[140px]" onClick={(e) => e.stopPropagation()}>
              <button onClick={() => startRename(conv)} className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700"><Pencil className="w-3 h-3" />Rename</button>
              {folders.length > 0 && (<div className="border-t border-gray-700 mt-1 pt-1">
                <p className="px-3 py-0.5 text-[10px] text-gray-500 uppercase">Move to</p>
                {folders.map((f) => (<button key={f.id} onClick={() => { onMove(conv.id, f.id); setMenuConvId(null); }} className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700"><FolderInput className="w-3 h-3" />{f.name}</button>))}
                {conv.folder_id && <button onClick={() => { onMove(conv.id, null); setMenuConvId(null); }} className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-gray-400 hover:bg-gray-700"><FolderInput className="w-3 h-3" />Remove from folder</button>}
              </div>)}
              <div className="border-t border-gray-700 mt-1 pt-1">
                <button onClick={() => { onCancel(conv.id); setMenuConvId(null); }} className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-red-400 hover:bg-gray-700"><Trash2 className="w-3 h-3" />Delete</button>
              </div>
            </div>)}
        </>
      )}
    </div>
  );

  const renderFolder = (folder) => (
    <div key={folder.id}>
      <div onClick={() => { setActiveFolder(activeFolderId === folder.id ? null : folder.id); toggleFolder(folder.id); }}
        className={`flex items-center gap-1.5 px-2 py-1.5 mx-1 rounded-lg cursor-pointer transition-colors group ${activeFolderId === folder.id ? 'bg-gray-800/60' : 'hover:bg-gray-800/30'}`}>
        <button className="p-0.5 text-gray-500">{collapsedFolders[folder.id] ? <ChevronRight className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}</button>
        {editingFolderId === folder.id ? (
          <div className="flex items-center gap-1 flex-1" onClick={(e) => e.stopPropagation()}>
            <input value={editFolderName} onChange={(e) => setEditFolderName(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') submitRenameFolder(); if (e.key === 'Escape') setEditingFolderId(null); }}
              onBlur={submitRenameFolder} className="flex-1 bg-gray-700 border border-gray-600 rounded px-1.5 py-0.5 text-xs text-white focus:outline-none" autoFocus />
          </div>
        ) : (<>
          <FolderOpen className="w-3.5 h-3.5 text-yellow-500/70 flex-shrink-0" />
          <span className="text-xs text-gray-300 truncate flex-1">{folder.name}</span>
          <span className="text-[10px] text-gray-600">{folderConvCounts[folder.id] || 0}</span>
          <div className="opacity-0 group-hover:opacity-100 flex gap-0.5 ml-1">
            <button onClick={(e) => { e.stopPropagation(); startRenameFolder(folder); }} className="p-0.5 rounded hover:bg-gray-700 text-gray-500 hover:text-gray-300"><Pencil className="w-3 h-3" /></button>
            <button onClick={(e) => { e.stopPropagation(); onDeleteFolder(folder.id); }} className="p-0.5 rounded hover:bg-gray-700 text-gray-500 hover:text-red-400"><Trash2 className="w-3 h-3" /></button>
          </div>
        </>)}
      </div>
      {!collapsedFolders[folder.id] && conversations.filter((c) => c.folder_id === folder.id && c.status === 'active').map(renderConv)}
    </div>
  );

  return (
    <div className="py-1">
      <div onClick={() => setActiveFolder(null)} className={`px-2 py-1.5 mx-1 rounded-lg cursor-pointer mb-1 ${!activeFolderId ? 'bg-gray-800/60' : 'hover:bg-gray-800/30'}`}>
        <span className="text-xs font-medium text-gray-400">All Chats</span></div>
      <div className="mb-2">
        <div className="flex items-center justify-between px-2 py-1">
          <span className="text-[10px] font-semibold text-gray-600 uppercase tracking-wider">Folders</span>
          <button onClick={() => setCreatingFolder(true)} className="p-0.5 rounded hover:bg-gray-700 text-gray-500 hover:text-gray-300"><FolderPlus className="w-3.5 h-3.5" /></button>
        </div>
        {creatingFolder && (
          <div className="px-2 mb-1 flex items-center gap-1">
            <input value={newFolderName} onChange={(e) => setNewFolderName(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') handleCreateFolder(); if (e.key === 'Escape') { setCreatingFolder(false); setNewFolderName(''); } }} onBlur={() => { if (!newFolderName.trim()) { setCreatingFolder(false); setNewFolderName(''); } }} placeholder="Folder name" className="flex-1 bg-gray-700 border border-gray-600 rounded px-2 py-0.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-primary-500" autoFocus />
            <button onClick={handleCreateFolder} className="p-0.5 text-green-400 hover:text-green-300"><Check className="w-3.5 h-3.5" /></button>
            <button onClick={() => { setCreatingFolder(false); setNewFolderName(''); }} className="p-0.5 text-gray-500 hover:text-gray-300"><X className="w-3.5 h-3.5" /></button>
          </div>)}
        {folders.map(renderFolder)}
      </div>
      <div className="px-2 py-1"><span className="text-[10px] font-semibold text-gray-600 uppercase tracking-wider">Chats</span></div>
      {filteredConvs.length === 0 ? <div className="px-4 py-6 text-center"><p className="text-[11px] text-gray-600">{activeFolderId ? 'No chats in this folder' : 'No conversations yet'}</p></div> : filteredConvs.map(renderConv)}
    </div>
  );
}
