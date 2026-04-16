'use client';

/**
 * Messages Page — FR-23, FR-24
 *
 * In-app messaging interface for farmer↔provider communication.
 * Split layout: conversation list sidebar + chat view.
 */

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import ConversationList from '../../components/ConversationList';
import ChatView from '../../components/ChatView';
import { apiGet } from '@/lib/api';

interface Conversation {
  id: string;
  participant_a_id: string;
  participant_b_id: string;
  service_request_id: string | null;
  last_message_at: string | null;
  status: string;
  created_at: string;
}

export default function MessagesPage() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConversations = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiGet('/api/v1/messages/conversations');
      setConversations(data);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const selectedConversation = conversations.find(c => c.id === selectedConvId);

  return (
    <div className="flex h-[calc(100vh-60px)] bg-cultivax-bg">
      {/* Conversation List Sidebar */}
      <div className={`
        w-full md:w-80 lg:w-96 border-r border-cultivax-border bg-cultivax-surface
        flex-shrink-0
        ${selectedConvId ? 'hidden md:flex md:flex-col' : 'flex flex-col'}
      `}>
        <div className="p-4 border-b border-cultivax-border">
          <h1 className="text-lg font-bold text-cultivax-text-primary flex items-center gap-2">
            <svg className="w-5 h-5 text-cultivax-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            Messages
          </h1>
          <p className="text-xs text-cultivax-text-muted mt-1">
            Communicate with service providers
          </p>
        </div>

        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="animate-spin w-6 h-6 border-2 border-cultivax-primary border-t-transparent rounded-full" />
          </div>
        ) : error ? (
          <div className="p-4 text-sm text-cultivax-danger">{error}</div>
        ) : (
          <ConversationList
            conversations={conversations}
            selectedId={selectedConvId}
            currentUserId={user?.id || ''}
            onSelect={(id: string) => setSelectedConvId(id)}
          />
        )}
      </div>

      {/* Chat View */}
      <div className={`
        flex-1 flex flex-col
        ${!selectedConvId ? 'hidden md:flex' : 'flex'}
      `}>
        {selectedConversation ? (
          <ChatView
            conversation={selectedConversation}
            currentUserId={user?.id || ''}
            onBack={() => setSelectedConvId(null)}
            onMessageSent={fetchConversations}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center bg-cultivax-bg">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-cultivax-primary/10 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-cultivax-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <p className="text-cultivax-text-muted text-sm">
                Select a conversation to start messaging
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
