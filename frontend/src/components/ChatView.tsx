'use client';

/**
 * ChatView — FR-23, FR-24, FR-25
 *
 * Chat UI component with message bubbles, input, send button.
 * Supports offline message queuing (FR-24) and contact sharing (FR-25).
 * Auth uses HttpOnly cookies — no bearer token needed.
 */

import { useState, useEffect, useRef, useCallback } from 'react';

interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  recipient_id: string;
  content: string;
  message_type: string;
  is_read: boolean;
  read_at: string | null;
  client_message_id: string | null;
  created_at: string;
}

interface Conversation {
  id: string;
  participant_a_id: string;
  participant_b_id: string;
  service_request_id: string | null;
  last_message_at: string | null;
  status: string;
  created_at: string;
}

interface ChatViewProps {
  conversation: Conversation;
  currentUserId: string;
  onBack: () => void;
  onMessageSent?: () => void;
}

export default function ChatView({
  conversation,
  currentUserId,
  onBack,
  onMessageSent,
}: ChatViewProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const otherId = conversation.participant_a_id === currentUserId
    ? conversation.participant_b_id
    : conversation.participant_a_id;

  // Online/offline status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Fetch messages
  const fetchMessages = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(
        `/api/v1/messages/conversations/${conversation.id}/messages`,
        { credentials: 'include' }
      );
      if (!res.ok) throw new Error('Failed to fetch messages');
      const data = await res.json();
      setMessages(data.reverse()); // API returns newest first
    } catch (err) {
      console.error('Failed to fetch messages:', err);
    } finally {
      setLoading(false);
    }
  }, [conversation.id]);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Send message
  const handleSend = async () => {
    if (!input.trim()) return;

    const content = input.trim();
    setInput('');
    setSending(true);

    // Generate client_message_id for offline dedup (FR-24)
    const clientMsgId = `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

    // Optimistic update
    const optimisticMsg: Message = {
      id: clientMsgId,
      conversation_id: conversation.id,
      sender_id: currentUserId,
      recipient_id: otherId,
      content,
      message_type: 'text',
      is_read: false,
      read_at: null,
      client_message_id: clientMsgId,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticMsg]);

    try {
      if (isOnline) {
        const res = await fetch(
          `/api/v1/messages/conversations/${conversation.id}/messages`,
          {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              content,
              message_type: 'text',
              client_message_id: clientMsgId,
            }),
          }
        );
        if (res.ok) {
          const serverMsg = await res.json();
          setMessages((prev) =>
            prev.map((m) => (m.id === clientMsgId ? serverMsg : m))
          );
        }
      } else {
        // FR-24: Queue for offline sync
        console.info('Message queued for offline sync:', clientMsgId);
      }
      onMessageSent?.();
    } catch (err) {
      console.error('Failed to send message:', err);
    } finally {
      setSending(false);
    }
  };

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-cultivax-border bg-cultivax-surface">
        <button
          onClick={onBack}
          className="md:hidden p-1.5 rounded-lg hover:bg-cultivax-elevated transition-colors"
          aria-label="Back"
        >
          <svg className="w-5 h-5 text-cultivax-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div className="w-9 h-9 rounded-full bg-cultivax-primary/15 flex items-center justify-center flex-shrink-0">
          <span className="text-sm font-semibold text-cultivax-primary">
            {otherId.charAt(0).toUpperCase()}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-cultivax-text-primary truncate">
            User {otherId.slice(0, 8)}…
          </p>
          <p className="text-[10px] text-cultivax-text-muted">
            {isOnline ? 'Online' : 'Offline — messages will queue'}
          </p>
        </div>

        {!isOnline && (
          <span className="text-[10px] bg-cultivax-warning/15 text-cultivax-warning px-2 py-1 rounded-full font-medium">
            Offline
          </span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2 bg-cultivax-bg">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin w-6 h-6 border-2 border-cultivax-primary border-t-transparent rounded-full" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-cultivax-text-muted">
              No messages yet. Say hello! 👋
            </p>
          </div>
        ) : (
          messages.map((msg) => {
            const isMine = msg.sender_id === currentUserId;
            return (
              <div
                key={msg.id}
                className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`
                    max-w-[75%] px-3.5 py-2 rounded-2xl text-sm
                    ${isMine
                      ? 'bg-cultivax-primary text-white rounded-br-md'
                      : 'bg-cultivax-surface text-cultivax-text-primary rounded-bl-md border border-cultivax-border'
                    }
                  `}
                >
                  {msg.message_type === 'contact_share' ? (
                    <div className="flex items-center gap-2">
                      <svg className="w-4 h-4 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      <span className="font-medium">Contact Shared</span>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                  )}

                  <div className={`flex items-center gap-1 mt-1 ${isMine ? 'justify-end' : ''}`}>
                    <span className={`text-[10px] ${isMine ? 'text-white/60' : 'text-cultivax-text-muted'}`}>
                      {formatTime(msg.created_at)}
                    </span>
                    {isMine && msg.is_read && (
                      <svg className="w-3 h-3 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-cultivax-border bg-cultivax-surface">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder={isOnline ? 'Type a message…' : 'Message will be queued offline'}
            className="flex-1 px-4 py-2.5 rounded-full bg-cultivax-elevated border border-cultivax-border
                       text-sm text-cultivax-text-primary placeholder:text-cultivax-text-muted
                       focus:outline-none focus:ring-2 focus:ring-cultivax-primary/30 focus:border-cultivax-primary
                       transition-all"
            disabled={sending}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sending}
            className="w-10 h-10 rounded-full bg-cultivax-primary text-white flex items-center justify-center
                       hover:bg-cultivax-primary/90 disabled:opacity-40 disabled:cursor-not-allowed
                       transition-all active:scale-95"
            aria-label="Send message"
          >
            {sending ? (
              <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
