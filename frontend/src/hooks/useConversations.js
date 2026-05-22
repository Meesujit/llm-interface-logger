import { useEffect, useState, useCallback } from 'react';
import client from '../api/client';
import useChatStore from '../store/chatStore';

export function useConversations() {
  const [loading, setLoading] = useState(false);
  const store = useChatStore();

  const fetchConversations = useCallback(async () => {
    setLoading(true);
    try { const res = await client.get('/conversations'); store.setConversations(res.data.conversations); }
    catch (err) { console.error('Failed to fetch conversations:', err); }
    finally { setLoading(false); }
  }, []);

  const fetchFolders = useCallback(async () => {
    try { const res = await client.get('/folders'); store.setFolders(res.data.folders); }
    catch (err) { console.error('Failed to fetch folders:', err); }
  }, []);

  const fetchMessages = async (convId) => {
    try { const res = await client.get(`/conversations/${convId}/messages`); store.setMessages(convId, res.data.messages); }
    catch (err) { console.error('Failed to fetch messages:', err); }
  };

  const renameConversation = async (convId, title) => {
    try { await client.patch(`/conversations/${convId}`, { title }); store.updateConversation(convId, { title }); }
    catch (err) { console.error('Failed to rename:', err); }
  };

  const moveConversation = async (convId, folderId) => {
    try { await client.patch(`/conversations/${convId}`, { folder_id: folderId || null }); store.updateConversation(convId, { folder_id: folderId || null }); }
    catch (err) { console.error('Failed to move conversation:', err); }
  };

  const cancelConversation = async (convId) => {
    try { await client.delete(`/conversations/${convId}`); store.cancelConversation(convId); }
    catch (err) { console.error('Failed to cancel conversation:', err); }
  };

  const resumeConversation = async (convId) => {
    try { await client.patch(`/conversations/${convId}`, { status: 'active' }); store.resumeConversation(convId); }
    catch (err) { console.error('Failed to resume:', err); }
  };

  const createFolder = async (name) => {
    try { const res = await client.post('/folders', { name }); store.addFolder(res.data); return res.data; }
    catch (err) { console.error('Failed to create folder:', err); }
  };

  const renameFolder = async (folderId, name) => {
    try { await client.patch(`/folders/${folderId}`, { name }); store.updateFolder(folderId, { name }); }
    catch (err) { console.error('Failed to rename folder:', err); }
  };

  const deleteFolder = async (folderId) => {
    try { await client.delete(`/folders/${folderId}`); store.removeFolder(folderId); }
    catch (err) { console.error('Failed to delete folder:', err); }
  };

  useEffect(() => { fetchConversations(); fetchFolders(); }, [fetchConversations, fetchFolders]);

  return { fetchConversations, fetchFolders, fetchMessages, renameConversation, moveConversation, cancelConversation, resumeConversation, createFolder, renameFolder, deleteFolder, loading };
}
